"""Inference orchestration.

Decouples the HTTP/workflow layer from the model. Two backends:

* ``mock``  – deterministic pseudo-inference (default). No torch required: it
  derives stable per-class probabilities from a hash of the image bytes and
  renders a simple Grad-CAM-style heatmap PNG. Lets the whole clinical workflow
  (upload → predict → review → finalize) run and be tested end-to-end with no ML
  dependencies.
* ``torch`` – delegates to ``ml.inference.predictor`` (DenseNet-121 + Grad-CAM).
  Imported lazily so the backend never hard-depends on torch.

Both return the same structured dict, so nothing downstream needs to know which
backend produced it.
"""
from __future__ import annotations

import hashlib
import os
import time

from app.constants import (
    FINDING_CODES,
    CRITICAL_FINDINGS,
    DEFAULT_THRESHOLDS,
    OVERALL_NORMAL,
    OVERALL_ABNORMAL_CRITICAL,
    OVERALL_ABNORMAL_NONCRITICAL,
)
from app.core.config import get_settings

settings = get_settings()


def _derive_probabilities(image_bytes: bytes) -> dict[str, float]:
    """Stable, image-dependent probabilities in [0,1] (mock backend)."""
    probs: dict[str, float] = {}
    for code in FINDING_CODES:
        digest = hashlib.sha256(image_bytes + code.encode()).hexdigest()
        probs[code] = int(digest[:8], 16) / 0xFFFFFFFF
    # Make "normal" inversely track the strongest abnormal signal so the output
    # is clinically coherent rather than random noise.
    strongest_abnormal = max(
        (p for c, p in probs.items() if c != "normal_no_critical_finding"), default=0.0
    )
    probs["normal_no_critical_finding"] = round(1.0 - strongest_abnormal, 4)
    return probs


def _overall_status(positives: list[str]) -> str:
    abnormal = [c for c in positives if c != "normal_no_critical_finding"]
    if any(c in CRITICAL_FINDINGS for c in abnormal):
        return OVERALL_ABNORMAL_CRITICAL
    if abnormal:
        return OVERALL_ABNORMAL_NONCRITICAL
    return OVERALL_NORMAL


def _render_mock_heatmap(out_path: str, code: str, intensity: float) -> None:
    """Render a lightweight pseudo Grad-CAM PNG (no torch)."""
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return  # heatmaps are optional; skip silently if PIL/numpy absent
    size = 224
    yy, xx = np.mgrid[0:size, 0:size]
    # Deterministic blob position per finding code.
    h = int(hashlib.sha256(code.encode()).hexdigest()[:6], 16)
    cx, cy = 40 + h % 140, 40 + (h >> 8) % 140
    sigma = 30 + (h >> 4) % 30
    blob = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * sigma**2)))
    blob = (blob * float(intensity)) ** 0.8
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = (blob * 255).astype(np.uint8)          # red
    rgba[..., 1] = ((1 - blob) * blob * 255).astype(np.uint8)  # a little green
    rgba[..., 3] = (blob * 200).astype(np.uint8)          # alpha overlay
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(out_path)


class InferenceService:
    def __init__(self, backend: str | None = None):
        self.backend = backend or settings.ml_backend

    def run(self, image_path: str, *, thresholds: dict[str, float] | None = None,
            heatmap_dir: str | None = None, study_id: str = "study") -> dict:
        thresholds = thresholds or DEFAULT_THRESHOLDS
        started = time.perf_counter()

        if self.backend == "xrv":
            return self._run_xrv(image_path, thresholds, heatmap_dir, study_id, started)
        if self.backend == "torch":
            return self._run_torch(image_path, thresholds, heatmap_dir, study_id, started)
        return self._run_mock(image_path, thresholds, heatmap_dir, study_id, started)

    # -- mock ---------------------------------------------------------------
    def _run_mock(self, image_path, thresholds, heatmap_dir, study_id, started):
        try:
            with open(image_path, "rb") as fh:
                image_bytes = fh.read()
        except OSError:
            image_bytes = study_id.encode()

        probs = _derive_probabilities(image_bytes)
        findings = []
        positives = []
        for code in FINDING_CODES:
            thr = float(thresholds.get(code, 0.5))
            prob = round(float(probs[code]), 4)
            is_pos = prob >= thr
            heatmap_path = None
            if is_pos and code != "normal_no_critical_finding" and heatmap_dir:
                heatmap_path = os.path.join(heatmap_dir, study_id, f"{code}.png")
                _render_mock_heatmap(heatmap_path, code, prob)
            if is_pos:
                positives.append(code)
            findings.append({
                "finding_code": code, "probability": prob, "threshold": thr,
                "is_positive": is_pos, "heatmap_path": heatmap_path,
            })

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "model_version": settings.model_version_name,
            "overall_status": _overall_status(positives),
            "inference_time_ms": elapsed_ms,
            "findings": findings,
        }

    # -- torch --------------------------------------------------------------
    def _run_torch(self, image_path, thresholds, heatmap_dir, study_id, started):
        # Imported lazily; only required when ML_BACKEND=torch.
        from app.ml_bridge import ensure_ml_importable

        ensure_ml_importable()
        from ml.inference.predictor import Predictor

        predictor = Predictor(settings.model_checkpoint)
        result = predictor.predict(
            image_path, thresholds=thresholds,
            heatmap_dir=os.path.join(heatmap_dir, study_id) if heatmap_dir else None,
        )
        positives = [f["finding_code"] for f in result["findings"] if f["is_positive"]]
        result["overall_status"] = _overall_status(positives)
        result["inference_time_ms"] = int((time.perf_counter() - started) * 1000)
        result["model_version"] = settings.model_version_name
        return result

    # -- xrv (TorchXRayVision pretrained — real chest X-ray reading) ---------
    def _run_xrv(self, image_path, thresholds, heatmap_dir, study_id, started):
        from app.ml_bridge import ensure_ml_importable

        ensure_ml_importable()
        from ml.inference.xrv_predictor import get_xrv_predictor

        predictor = get_xrv_predictor(settings.xrv_weights)
        result = predictor.predict(
            image_path, thresholds=thresholds,
            heatmap_dir=os.path.join(heatmap_dir, study_id) if heatmap_dir else None,
        )
        positives = [f["finding_code"] for f in result["findings"] if f["is_positive"]]
        result["overall_status"] = _overall_status(positives)
        result["inference_time_ms"] = int((time.perf_counter() - started) * 1000)
        return result
