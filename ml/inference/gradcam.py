"""Grad-CAM heatmap generation for explainability.

Produces a per-finding heatmap PNG (RGBA overlay) highlighting the image regions
that most contributed to a positive prediction. Heatmaps are an interpretability
aid for the radiologist, NOT diagnostic proof.
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn.functional as F


class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        target_layer.register_forward_hook(self._save_activation)
        target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, inp, out):
        self.activations = out.detach()

    def _save_gradient(self, module, grad_in, grad_out):
        self.gradients = grad_out[0].detach()

    def __call__(self, input_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        self.model.zero_grad()
        logits = self.model(input_tensor)
        logits[0, class_idx].backward(retain_graph=True)

        # weight each activation channel by its mean gradient.
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, size=input_tensor.shape[2:], mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (np.ptp(cam) + 1e-6)
        return cam


def default_target_layer(model, backbone: str):
    if backbone == "densenet121":
        return model.features.denseblock4
    if backbone == "resnet50":
        return model.layer4
    raise ValueError(f"No default Grad-CAM layer for backbone {backbone}")


def save_heatmap(cam: np.ndarray, out_path: str) -> str:
    from PIL import Image

    heat = (cam * 255).astype(np.uint8)
    rgba = np.zeros((*heat.shape, 4), dtype=np.uint8)
    rgba[..., 0] = heat                       # red channel
    rgba[..., 1] = ((255 - heat) * (heat / 255.0)).astype(np.uint8)
    rgba[..., 3] = (cam * 200).astype(np.uint8)  # transparency follows intensity
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(out_path)
    return out_path
