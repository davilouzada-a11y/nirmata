"""Real chest X-ray inference using TorchXRayVision pretrained models.

This is the "actually reads the X-ray" backend: it loads a DenseNet-121 trained
on ~1M real chest radiographs (NIH ChestX-ray14, CheXpert, MIMIC-CXR, PadChest,
Google, OpenI, Kaggle) and outputs genuine per-pathology probabilities — no
training required, runs on CPU.

It exposes the same `predict()` contract as the project's own `Predictor`, so the
backend's InferenceService is agnostic to which model produced the result.

IMPORTANT: still advisory, not a certified diagnosis. The pretrained model has
domain shift vs. any given site and its probabilities are not locally calibrated;
mandatory human review remains the rule.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

# Map our MVP finding codes → TorchXRayVision pathology names.
XRV_PATHOLOGY = {
    "pneumothorax": "Pneumothorax",
    "pleural_effusion": "Effusion",
    "consolidation": "Consolidation",
    "lung_opacity": "Lung Opacity",
    "cardiomegaly": "Cardiomegaly",
}
ABNORMAL_CODES = list(XRV_PATHOLOGY.keys())


def _load_grayscale_uint8(image_path: str) -> np.ndarray:
    """Load PNG/JPG or (de-identified) DICOM as an HxW uint8 array."""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".dcm", ".dicom"):
        import pydicom
        from ml.preprocessing.windowing import to_display_uint8

        ds = pydicom.dcmread(image_path, force=True)
        return to_display_uint8(ds)
    from PIL import Image

    return np.array(Image.open(image_path).convert("L"), dtype=np.uint8)


class XRVPredictor:
    def __init__(self, weights: str = "densenet121-res224-all"):
        import torch
        import torchxrayvision as xrv

        self.torch = torch
        self.xrv = xrv
        self.weights = weights
        self.model = xrv.models.DenseNet(weights=weights)
        self.model.eval()
        self.model_version = f"cxr-torchxrayvision-{weights}"
        self.pathologies = list(self.model.pathologies)

    # -- preprocessing per the TorchXRayVision convention --------------------
    def _preprocess(self, image_path: str):
        import torchvision

        img = _load_grayscale_uint8(image_path).astype(np.float32)
        img = self.xrv.datasets.normalize(img, 255)      # → [-1024, 1024]
        img = img[None, ...]                             # add channel dim (1xHxW)
        tf = torchvision.transforms.Compose([
            self.xrv.datasets.XRayCenterCrop(),
            self.xrv.datasets.XRayResizer(224),
        ])
        img = tf(img)
        return self.torch.from_numpy(img)[None, ...]     # 1x1x224x224

    def _probs(self, x) -> dict[str, float]:
        with self.torch.no_grad():
            out = self.model(x)[0]
        return {p: float(v) for p, v in zip(self.pathologies, out.tolist())}

    def _heatmap(self, x, pathology: str, out_path: str) -> str | None:
        """Best-effort Grad-CAM; returns None if it can't be produced."""
        try:
            from ml.inference.gradcam import GradCAM, save_heatmap

            target = getattr(self.model.features, "denseblock4", None) or self.model.features
            cam = GradCAM(self.model, target)
            idx = self.pathologies.index(pathology)
            heat = cam(x, idx)
            return save_heatmap(heat, out_path)
        except Exception:
            return None

    def raw_pathology_scores(self, image_path: str) -> dict[str, float]:
        """All 18 TorchXRayVision pathology probabilities (for validation/analysis)."""
        return self._probs(self._preprocess(image_path))

    def predict(self, image_path: str, *, thresholds: dict | None = None,
                heatmap_dir: str | None = None) -> dict:
        thresholds = thresholds or {}
        x = self._preprocess(image_path)
        probs = self._probs(x)

        findings = []
        abnormal_probs = []
        for code in ABNORMAL_CODES:
            prob = round(probs[XRV_PATHOLOGY[code]], 4)
            abnormal_probs.append(prob)
            thr = float(thresholds.get(code, 0.5))
            is_pos = prob >= thr
            heatmap_path = None
            if is_pos and heatmap_dir:
                heatmap_path = self._heatmap(x, XRV_PATHOLOGY[code],
                                             os.path.join(heatmap_dir, f"{code}.png"))
            findings.append({
                "finding_code": code, "probability": prob, "threshold": thr,
                "is_positive": is_pos, "heatmap_path": heatmap_path,
            })

        # No native "normal" class → derive from the strongest abnormal signal.
        normal_prob = round(1.0 - max(abnormal_probs, default=0.0), 4)
        normal_thr = float(thresholds.get("normal_no_critical_finding", 0.5))
        findings.insert(0, {
            "finding_code": "normal_no_critical_finding", "probability": normal_prob,
            "threshold": normal_thr, "is_positive": normal_prob >= normal_thr,
            "heatmap_path": None,
        })

        return {"model_version": self.model_version, "findings": findings}


@lru_cache(maxsize=2)
def get_xrv_predictor(weights: str = "densenet121-res224-all") -> XRVPredictor:
    """Cached predictor so the (heavy) weights load once per process."""
    return XRVPredictor(weights=weights)
