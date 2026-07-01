"""Smoke test for the real (TorchXRayVision) inference backend.

Skipped automatically when torch / torchxrayvision aren't installed, or when the
pretrained weights can't be downloaded (offline CI) — the backend is opt-in and
heavy, so its deps aren't required for the default test run.
"""
import io
import os
import tempfile

import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("torchxrayvision")


@pytest.fixture(scope="module")
def predictor():
    from ml.inference.xrv_predictor import get_xrv_predictor
    try:
        return get_xrv_predictor()
    except Exception as err:  # weights download failed (no network) → skip
        pytest.skip(f"TorchXRayVision weights unavailable: {err}")


def _gradient_png() -> str:
    from PIL import Image

    arr = np.tile(np.linspace(0, 255, 256, dtype=np.uint8), (256, 1))
    path = os.path.join(tempfile.mkdtemp(), "cxr.png")
    Image.fromarray(arr, "L").save(path)
    return path


def test_xrv_reads_image_and_returns_findings(predictor):
    path = _gradient_png()
    result = predictor.predict(path, heatmap_dir=None)

    codes = [f["finding_code"] for f in result["findings"]]
    assert codes[0] == "normal_no_critical_finding"
    for code in ["pneumothorax", "pleural_effusion", "consolidation", "cardiomegaly"]:
        assert code in codes

    for f in result["findings"]:
        assert 0.0 <= f["probability"] <= 1.0
        assert isinstance(f["is_positive"], bool)

    assert result["model_version"].startswith("cxr-torchxrayvision-")


def test_normal_is_inverse_of_strongest_abnormal(predictor):
    path = _gradient_png()
    result = predictor.predict(path, heatmap_dir=None)
    findings = {f["finding_code"]: f["probability"] for f in result["findings"]}
    strongest = max(findings[c] for c in
                    ["pneumothorax", "pleural_effusion", "consolidation", "cardiomegaly"])
    assert abs(findings["normal_no_critical_finding"] - (1.0 - strongest)) < 1e-3
