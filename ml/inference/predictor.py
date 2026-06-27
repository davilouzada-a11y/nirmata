"""Production inference: load a checkpoint, classify a chest X-ray, and emit
per-finding probabilities plus Grad-CAM heatmaps for positive findings.

Returns the same dict shape the backend's InferenceService expects, so the
FastAPI layer is agnostic to mock vs. torch.
"""
from __future__ import annotations

import os

import torch

from ml.inference.preprocess import load_image, to_tensor
from ml.inference.gradcam import GradCAM, default_target_layer, save_heatmap


class Predictor:
    def __init__(self, checkpoint_path: str, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.findings = ckpt["findings"]
        self.thresholds = ckpt.get("thresholds", {})
        self.backbone = ckpt["backbone"]
        self.model_version = ckpt.get("model_version", "unknown")

        from ml.training.train import build_model

        self.model = build_model(self.backbone, len(self.findings), pretrained=False)
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.to(self.device).eval()
        self.cam = GradCAM(self.model, default_target_layer(self.model, self.backbone))

    def predict(self, image_path: str, *, thresholds: dict | None = None,
                heatmap_dir: str | None = None) -> dict:
        thresholds = thresholds or self.thresholds
        image = load_image(image_path)
        x = to_tensor(image).to(self.device)

        with torch.no_grad():
            probs = torch.sigmoid(self.model(x)).squeeze(0).cpu().tolist()

        findings = []
        for i, code in enumerate(self.findings):
            thr = float(thresholds.get(code, 0.5))
            prob = round(float(probs[i]), 4)
            is_pos = prob >= thr
            heatmap_path = None
            if is_pos and code != "normal_no_critical_finding" and heatmap_dir:
                cam = self.cam(x, i)
                heatmap_path = os.path.join(heatmap_dir, f"{code}.png")
                save_heatmap(cam, heatmap_path)
            findings.append({
                "finding_code": code, "probability": prob, "threshold": thr,
                "is_positive": is_pos, "heatmap_path": heatmap_path,
            })

        return {"model_version": self.model_version, "findings": findings}
