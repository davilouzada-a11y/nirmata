"""Convert raw DICOM pixels to a display-ready 8-bit image.

Applies the Modality LUT (RescaleSlope/Intercept) and the VOI LUT
(WindowCenter/WindowWidth), handles MONOCHROME1 inversion, and falls back to
min-max scaling when no window is specified.
"""
from __future__ import annotations

import numpy as np


def apply_modality_lut(arr: np.ndarray, ds) -> np.ndarray:
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    intercept = float(getattr(ds, "RescaleIntercept", 0) or 0)
    return arr.astype(np.float32) * slope + intercept


def _first(value):
    # WindowCenter/Width may be a single value or a MultiValue list.
    if value is None:
        return None
    try:
        return float(value[0])
    except (TypeError, IndexError):
        return float(value)


def apply_voi(arr: np.ndarray, ds) -> np.ndarray:
    """Return float array scaled to [0, 1]."""
    center = _first(getattr(ds, "WindowCenter", None))
    width = _first(getattr(ds, "WindowWidth", None))

    if center is not None and width and width > 0:
        lo = center - width / 2.0
        hi = center + width / 2.0
    else:
        lo, hi = float(arr.min()), float(arr.max())

    if hi <= lo:
        hi = lo + 1.0
    out = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    if str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2")) == "MONOCHROME1":
        out = 1.0 - out  # MONOCHROME1: high value = dark
    return out


def to_display_uint8(ds) -> np.ndarray:
    """Full DICOM → 8-bit grayscale display pipeline."""
    arr = ds.pixel_array
    arr = apply_modality_lut(arr, ds)
    arr01 = apply_voi(arr, ds)
    return (arr01 * 255.0).astype(np.uint8)
