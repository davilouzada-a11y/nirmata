"""Per-finding decision-threshold calibration.

The default 0.5 thresholds over-flag normals (low specificity). This module
picks better operating points from labeled scores. To avoid the circularity of
tuning and evaluating on the same data, callers should calibrate on a training
split and report on a held-out split (see calibrate_covid.py, which uses k-fold
cross-validation).

Two regimes, because our validation set only has positives for some findings:

* **signal findings** (positives available, e.g. lung_opacity/consolidation):
  pick the highest threshold that still keeps sensitivity ≥ target — i.e. the
  most specific operating point that doesn't sacrifice recall.
* **specificity-only findings** (no positives here, e.g. effusion/cardiomegaly):
  pick a threshold from the *normal* score distribution so their false-positive
  rate on normals stays within a small budget. Critical findings (pneumothorax)
  are capped low so we never blind a finding we couldn't measure recall for.
"""
from __future__ import annotations

import numpy as np


def target_sensitivity_threshold(y: np.ndarray, s: np.ndarray, target: float) -> float:
    """Highest threshold with sensitivity ≥ target (→ maximal specificity)."""
    y = np.asarray(y)
    s = np.asarray(s)
    pos = s[y == 1]
    if len(pos) == 0:
        return 0.5
    best = float(np.min(s))
    for t in np.unique(s):
        sens = float((pos >= t).mean())
        if sens >= target:
            best = float(t)  # monotonic: keep the largest t still meeting target
        else:
            break
    return best


def normal_fpr_threshold(normal_scores: np.ndarray, fpr_budget: float) -> float:
    """Threshold so that ≤ fpr_budget of normals score above it."""
    normal_scores = np.asarray(normal_scores)
    if len(normal_scores) == 0:
        return 0.5
    return float(np.quantile(normal_scores, 1.0 - fpr_budget))


def calibrate(scores: dict[str, np.ndarray], y_pneu: np.ndarray, y_norm: np.ndarray, *,
              signal_findings: list[str], critical_findings: set[str],
              target_sensitivity: float = 0.90, normal_fpr_budget: float = 0.05,
              critical_cap: float = 0.45, default: float = 0.50) -> dict[str, float]:
    """Return calibrated per-finding thresholds."""
    y_pneu = np.asarray(y_pneu)
    y_norm = np.asarray(y_norm)
    normal_mask = y_norm == 1
    thr: dict[str, float] = {}

    for finding, s in scores.items():
        s = np.asarray(s)
        if finding in signal_findings:
            # positives = pneumonia, negatives = normal
            y = np.where(y_pneu == 1, 1, 0)
            thr[finding] = target_sensitivity_threshold(y, s, target_sensitivity)
        else:
            t = normal_fpr_threshold(s[normal_mask], normal_fpr_budget)
            if finding in critical_findings:
                t = min(t, critical_cap)  # don't raise a critical finding's bar blindly
            thr[finding] = t
    return thr


def triage_metrics(scores: dict[str, np.ndarray], thresholds: dict[str, float],
                   y_pneu: np.ndarray, y_norm: np.ndarray,
                   abnormal_findings: list[str]) -> dict:
    """Evaluate OR-of-findings triage: sensitivity on pneumonia, specificity on normal."""
    y_pneu = np.asarray(y_pneu)
    y_norm = np.asarray(y_norm)
    pred_abnormal = np.zeros(len(y_pneu), dtype=bool)
    for f in abnormal_findings:
        pred_abnormal |= np.asarray(scores[f]) >= thresholds.get(f, 0.5)

    pneu = y_pneu == 1
    norm = y_norm == 1
    sens = float(pred_abnormal[pneu].mean()) if pneu.any() else float("nan")
    spec = float((~pred_abnormal[norm]).mean()) if norm.any() else float("nan")
    return {"sensitivity": sens, "specificity": spec,
            "n_pos": int(pneu.sum()), "n_neg": int(norm.sum())}
