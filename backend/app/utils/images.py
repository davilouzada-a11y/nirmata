"""Synthetic chest-X-ray-like image generation for demos and tests.

These are NOT real radiographs — they are procedurally generated grayscale
images that merely *look* chest-X-ray-ish (dark lung fields, a brighter
mediastinum/spine, a rib-cage gradient) so the viewer, heatmap overlay and
worklist have plausible content without shipping any patient data.
"""
from __future__ import annotations

import io
import math


def synthetic_cxr(seed: int = 0, size: int = 512) -> bytes:
    """Return PNG bytes of a deterministic synthetic chest radiograph."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype("float32")
    cx = size / 2.0

    # Base soft-tissue background.
    img = np.full((size, size), 60.0, dtype="float32")

    # Two dark lung fields (ellipses) left/right of the midline.
    for sign in (-1, 1):
        lx = cx + sign * size * 0.22
        ly = size * 0.52
        ex = ((xx - lx) / (size * 0.17)) ** 2
        ey = ((yy - ly) / (size * 0.27)) ** 2
        lung = np.clip(1.0 - (ex + ey), 0, 1)
        img -= lung * 45.0  # darker = more air

    # Bright mediastinum / spine column in the middle.
    spine = np.exp(-((xx - cx) ** 2) / (2 * (size * 0.045) ** 2))
    img += spine * 70.0

    # Rib gradient (faint horizontal bands).
    ribs = 8 + 6 * np.sin((yy / size) * math.pi * 9 + seed)
    img += ribs * 0.6

    # A random "finding" blob in one lung to give heatmaps something to point at.
    bx = cx + rng.choice([-1, 1]) * size * (0.18 + 0.06 * rng.random())
    by = size * (0.4 + 0.25 * rng.random())
    br = size * (0.04 + 0.04 * rng.random())
    blob = np.exp(-(((xx - bx) ** 2 + (yy - by) ** 2) / (2 * br ** 2)))
    img += blob * (30 + 40 * rng.random())

    img += rng.normal(0, 4, size=(size, size))  # sensor noise
    img = np.clip(img, 0, 255).astype("uint8")

    buf = io.BytesIO()
    Image.fromarray(img, "L").save(buf, format="PNG")
    return buf.getvalue()
