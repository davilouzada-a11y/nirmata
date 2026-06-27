"""Image preprocessing shared by inference and Grad-CAM.

Accepts PNG/JPG or DICOM and returns a normalized 3-channel tensor plus the
display image (for heatmap overlay).
"""
from __future__ import annotations

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

_NORM = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])


def load_image(path: str) -> Image.Image:
    if path.lower().endswith((".dcm", ".dicom")):
        import pydicom

        ds = pydicom.dcmread(path)
        arr = ds.pixel_array.astype(np.float32)
        arr = (arr - arr.min()) / (np.ptp(arr) + 1e-6) * 255.0
        return Image.fromarray(arr.astype(np.uint8)).convert("L")
    return Image.open(path).convert("L")


def to_tensor(image: Image.Image, image_size: int = 224) -> torch.Tensor:
    tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        _NORM,
    ])
    return tf(image).unsqueeze(0)  # add batch dim
