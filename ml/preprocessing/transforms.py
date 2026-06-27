"""Model-input transforms.

Prefers MONAI's medical-imaging transforms (the standard for this domain); falls
back to a dependency-free numpy/PIL implementation when MONAI isn't installed, so
the pipeline runs everywhere. Both produce a CxHxW float32 tensor-like array
normalized for an ImageNet-pretrained backbone.

The MONAI path is also the recommended place to add training-time augmentation
(see ml/README and the "data augmentation no MONAI" topic): RandFlip,
RandRotate, RandAdjustContrast, RandGaussianNoise, etc.
"""
from __future__ import annotations

import numpy as np

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def monai_available() -> bool:
    try:
        import monai  # noqa: F401
        return True
    except Exception:
        return False


def build_monai_eval_transforms(image_size: int = 224):
    """MONAI Compose for inference (deterministic)."""
    from monai.transforms import (
        Compose, EnsureChannelFirst, ScaleIntensity, Resize, RepeatChannel, NormalizeIntensity,
    )

    return Compose([
        EnsureChannelFirst(channel_dim="no_channel"),
        ScaleIntensity(),                       # → [0, 1]
        Resize(spatial_size=(image_size, image_size)),
        RepeatChannel(repeats=3),               # grayscale → 3-channel
        NormalizeIntensity(subtrahend=IMAGENET_MEAN[:, None, None],
                           divisor=IMAGENET_STD[:, None, None], channel_wise=True),
    ])


def build_monai_train_transforms(image_size: int = 224):
    """MONAI Compose for training (with augmentation)."""
    from monai.transforms import (
        Compose, EnsureChannelFirst, ScaleIntensity, Resize, RepeatChannel,
        RandFlip, RandRotate, RandAdjustContrast, RandGaussianNoise, NormalizeIntensity,
    )

    return Compose([
        EnsureChannelFirst(channel_dim="no_channel"),
        ScaleIntensity(),
        Resize(spatial_size=(image_size, image_size)),
        RandFlip(prob=0.5, spatial_axis=1),
        RandRotate(range_x=0.12, prob=0.5, keep_size=True),
        RandAdjustContrast(prob=0.3, gamma=(0.9, 1.1)),
        RandGaussianNoise(prob=0.2, std=0.02),
        RepeatChannel(repeats=3),
        NormalizeIntensity(subtrahend=IMAGENET_MEAN[:, None, None],
                           divisor=IMAGENET_STD[:, None, None], channel_wise=True),
    ])


def numpy_eval_transform(gray01: np.ndarray, image_size: int = 224) -> np.ndarray:
    """Dependency-free fallback: HxW float[0,1] → 3xHxW normalized float32."""
    from PIL import Image

    img = Image.fromarray((gray01 * 255).astype(np.uint8)).resize(
        (image_size, image_size), Image.BILINEAR
    )
    x = np.asarray(img, dtype=np.float32) / 255.0          # HxW
    x = np.stack([x, x, x], axis=0)                        # 3xHxW
    x = (x - IMAGENET_MEAN[:, None, None]) / IMAGENET_STD[:, None, None]
    return x.astype(np.float32)


def preprocess_for_model(gray01: np.ndarray, image_size: int = 224, use_monai: bool | None = None):
    """Return a model-ready CxHxW array, using MONAI when available."""
    use_monai = monai_available() if use_monai is None else use_monai
    if use_monai:
        tf = build_monai_eval_transforms(image_size)
        return np.asarray(tf(gray01))
    return numpy_eval_transform(gray01, image_size)
