"""Clinical evaluation metrics for the multi-label CXR model.

Reports per-class AUROC, AUPRC, sensitivity (recall), specificity and F1 — not
just accuracy, because accuracy hides poor performance on rare critical findings.
"""
from __future__ import annotations

import numpy as np
import torch


@torch.no_grad()
def _collect(model, loader, device):
    model.eval()
    all_probs, all_targets = [], []
    for x, y in loader:
        x = x.to(device)
        probs = torch.sigmoid(model(x)).cpu().numpy()
        all_probs.append(probs)
        all_targets.append(y.numpy())
    return np.concatenate(all_probs), np.concatenate(all_targets)


def _safe_auroc(y_true, y_score):
    from sklearn.metrics import roc_auc_score

    if len(np.unique(y_true)) < 2:
        return float("nan")  # AUROC undefined when only one class present
    return roc_auc_score(y_true, y_score)


def evaluate(model, loader, findings: list[str], device: str,
             thresholds: dict | None = None) -> dict:
    from sklearn.metrics import average_precision_score, f1_score

    probs, targets = _collect(model, loader, device)
    per_class = {}
    aurocs = []
    for i, code in enumerate(findings):
        thr = (thresholds or {}).get(code, 0.5)
        y_true = targets[:, i]
        y_score = probs[:, i]
        y_pred = (y_score >= thr).astype(int)

        tp = int(((y_pred == 1) & (y_true == 1)).sum())
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        tn = int(((y_pred == 0) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())

        sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
        specificity = tn / (tn + fp) if (tn + fp) else float("nan")
        auroc = _safe_auroc(y_true, y_score)
        if not np.isnan(auroc):
            aurocs.append(auroc)

        per_class[code] = {
            "auroc": auroc,
            "auprc": average_precision_score(y_true, y_score) if y_true.sum() else float("nan"),
            "sensitivity": sensitivity,
            "specificity": specificity,
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "fnr": (fn / (tp + fn)) if (tp + fn) else float("nan"),
        }

    return {"per_class": per_class, "macro_auroc": float(np.mean(aurocs)) if aurocs else 0.0}


if __name__ == "__main__":
    import argparse
    import yaml
    from torch.utils.data import DataLoader
    from ml.training.dataset import ChestXrayDataset
    from ml.training.train import build_model

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="ml/training/config.yaml")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--split", default="test")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt = torch.load(args.checkpoint, map_location=device)
    model = build_model(ckpt["backbone"], len(ckpt["findings"]), pretrained=False).to(device)
    model.load_state_dict(ckpt["state_dict"])

    ds = ChestXrayDataset(cfg["data"]["images_dir"], cfg["data"]["labels_csv"],
                          ckpt["findings"], args.split, cfg["data"]["image_size"])
    loader = DataLoader(ds, batch_size=cfg["train"]["batch_size"])
    results = evaluate(model, loader, ckpt["findings"], device, ckpt.get("thresholds"))
    import json
    print(json.dumps(results, indent=2))
