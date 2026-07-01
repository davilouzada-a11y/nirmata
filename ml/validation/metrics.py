"""Clinical validation metrics with bootstrap confidence intervals.

Deliberately reports more than accuracy: AUROC (+95% CI), AUPRC, and
sensitivity/specificity/PPV/NPV at a given operating threshold — because in
radiology missing a positive matters more than overall accuracy.
"""
from __future__ import annotations

import numpy as np


def _auroc(y, s):
    from sklearn.metrics import roc_auc_score

    y = np.asarray(y)
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def bootstrap_auroc_ci(y, s, n: int = 1000, seed: int = 0, alpha: float = 0.05):
    """Percentile bootstrap 95% CI for AUROC."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    s = np.asarray(s)
    idx = np.arange(len(y))
    stats = []
    for _ in range(n):
        b = rng.choice(idx, size=len(idx), replace=True)
        if len(np.unique(y[b])) < 2:
            continue
        stats.append(_auroc(y[b], s[b]))
    if not stats:
        return (float("nan"), float("nan"))
    lo = float(np.percentile(stats, 100 * alpha / 2))
    hi = float(np.percentile(stats, 100 * (1 - alpha / 2)))
    return (lo, hi)


def binary_at_threshold(y, s, thr: float) -> dict:
    y = np.asarray(y)
    pred = (np.asarray(s) >= thr).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    return {
        "threshold": thr,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "sensitivity": tp / (tp + fn) if (tp + fn) else float("nan"),
        "specificity": tn / (tn + fp) if (tn + fp) else float("nan"),
        "ppv": tp / (tp + fp) if (tp + fp) else float("nan"),
        "npv": tn / (tn + fn) if (tn + fn) else float("nan"),
    }


def evaluate_score(y, s, thr: float, *, seed: int = 0) -> dict:
    """Full metric bundle for one continuous score vs. binary ground truth."""
    from sklearn.metrics import average_precision_score

    y = np.asarray(y)
    s = np.asarray(s)
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    auroc = _auroc(y, s)
    ci = bootstrap_auroc_ci(y, s, seed=seed)
    auprc = float(average_precision_score(y, s)) if n_pos and n_neg else float("nan")
    out = {
        "n": int(len(y)), "n_pos": n_pos, "n_neg": n_neg,
        "auroc": auroc, "auroc_ci95": ci, "auprc": auprc,
    }
    out.update(binary_at_threshold(y, s, thr))
    return out
