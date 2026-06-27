"""Chest X-ray multi-label dataset.

Reads a labels CSV of the form:

    image_id,patient_id,view,split,normal_no_critical_finding,pneumothorax,\
        pleural_effusion,consolidation,cardiomegaly

Each finding column holds 0/1. Splits: train | val | test.
"""
from __future__ import annotations

import os

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


def build_transforms(image_size: int, train: bool):
    # ImageNet normalization (DenseNet/ResNet are pretrained on it).
    norm = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    if train:
        return transforms.Compose([
            transforms.Grayscale(num_output_channels=3),
            transforms.Resize((image_size, image_size)),
            transforms.RandomAffine(degrees=7, translate=(0.05, 0.05)),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            norm,
        ])
    return transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        norm,
    ])


class ChestXrayDataset(Dataset):
    def __init__(self, images_dir: str, labels_csv: str, findings: list[str],
                 split: str, image_size: int = 224):
        df = pd.read_csv(labels_csv)
        self.df = df[df["split"] == split].reset_index(drop=True)
        self.images_dir = images_dir
        self.findings = findings
        self.tf = build_transforms(image_size, train=(split == "train"))

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = os.path.join(self.images_dir, f"{row['image_id']}.png")
        image = Image.open(path).convert("L")
        x = self.tf(image)
        y = torch.tensor([float(row[c]) for c in self.findings], dtype=torch.float32)
        return x, y

    def positive_counts(self) -> torch.Tensor:
        """Per-class positive counts, used to weight the loss for imbalance."""
        return torch.tensor([self.df[c].sum() for c in self.findings], dtype=torch.float32)
