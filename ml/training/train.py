"""Train a multi-label chest X-ray classifier (DenseNet-121 by default).

Usage:
    python -m ml.training.train --config ml/training/config.yaml

Follows the blueprint pipeline: weighted BCE for class imbalance, AdamW +
cosine schedule, per-epoch validation, best-checkpoint saving by macro-AUROC.
"""
from __future__ import annotations

import argparse
import os

import torch
import yaml
from torch.utils.data import DataLoader

from ml.training.dataset import ChestXrayDataset
from ml.training.evaluate import evaluate


def build_model(backbone: str, num_classes: int, pretrained: bool):
    from torchvision import models

    if backbone == "densenet121":
        net = models.densenet121(weights="DEFAULT" if pretrained else None)
        net.classifier = torch.nn.Linear(net.classifier.in_features, num_classes)
    elif backbone == "resnet50":
        net = models.resnet50(weights="DEFAULT" if pretrained else None)
        net.fc = torch.nn.Linear(net.fc.in_features, num_classes)
    else:
        raise ValueError(f"Unsupported backbone: {backbone}")
    return net


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        running += loss.item() * x.size(0)
    return running / len(loader.dataset)


def main(config_path: str):
    with open(config_path) as fh:
        cfg = yaml.safe_load(fh)

    device = cfg["train"]["device"] if torch.cuda.is_available() else "cpu"
    findings = cfg["findings"]
    image_size = cfg["data"]["image_size"]

    train_ds = ChestXrayDataset(cfg["data"]["images_dir"], cfg["data"]["labels_csv"],
                                findings, "train", image_size)
    val_ds = ChestXrayDataset(cfg["data"]["images_dir"], cfg["data"]["labels_csv"],
                              findings, "val", image_size)

    train_loader = DataLoader(train_ds, batch_size=cfg["train"]["batch_size"], shuffle=True,
                              num_workers=cfg["train"]["num_workers"])
    val_loader = DataLoader(val_ds, batch_size=cfg["train"]["batch_size"], shuffle=False,
                            num_workers=cfg["train"]["num_workers"])

    model = build_model(cfg["model"]["backbone"], cfg["model"]["num_classes"],
                        cfg["model"]["pretrained"]).to(device)

    # Weighted BCE: pos_weight = neg/pos per class to counter imbalance.
    pos = train_ds.positive_counts().clamp(min=1)
    neg = len(train_ds) - pos
    pos_weight = (neg / pos).to(device)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["train"]["lr"],
                                  weight_decay=cfg["train"]["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg["train"]["epochs"])

    ckpt_dir = cfg["train"]["checkpoint_dir"]
    os.makedirs(ckpt_dir, exist_ok=True)
    best_auroc = -1.0

    for epoch in range(cfg["train"]["epochs"]):
        loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        metrics = evaluate(model, val_loader, findings, device)
        scheduler.step()
        macro_auroc = metrics["macro_auroc"]
        print(f"epoch {epoch+1}/{cfg['train']['epochs']} "
              f"loss={loss:.4f} val_macro_auroc={macro_auroc:.4f}")

        if macro_auroc > best_auroc:
            best_auroc = macro_auroc
            ckpt_path = os.path.join(ckpt_dir, f"{cfg['train']['model_version']}.pt")
            torch.save({
                "state_dict": model.state_dict(),
                "backbone": cfg["model"]["backbone"],
                "findings": findings,
                "thresholds": cfg["thresholds"],
                "model_version": cfg["train"]["model_version"],
                "val_macro_auroc": macro_auroc,
            }, ckpt_path)
            print(f"  ↳ saved best checkpoint: {ckpt_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="ml/training/config.yaml")
    main(ap.parse_args().config)
