"""Unit tests for threshold calibration (pure numpy — no torch/network)."""
import numpy as np

from ml.validation.calibrate import (
    target_sensitivity_threshold,
    normal_fpr_threshold,
    calibrate,
    triage_metrics,
)


def test_target_sensitivity_threshold_keeps_recall():
    # positives score high, negatives low → a mid threshold keeps sens=1.
    y = np.array([1, 1, 1, 0, 0, 0])
    s = np.array([0.9, 0.8, 0.7, 0.2, 0.1, 0.3])
    t = target_sensitivity_threshold(y, s, target=1.0)
    assert (s[y == 1] >= t).mean() == 1.0          # all positives still caught
    assert t > 0.3                                  # and it clears the negatives' top


def test_target_sensitivity_allows_more_specificity_when_target_lower():
    y = np.array([1, 1, 1, 0, 0, 0])
    s = np.array([0.9, 0.8, 0.4, 0.2, 0.1, 0.3])
    t_high = target_sensitivity_threshold(y, s, target=1.0)   # must keep the 0.4 positive
    t_low = target_sensitivity_threshold(y, s, target=0.66)   # may drop it → higher t
    assert t_low >= t_high


def test_normal_fpr_threshold_controls_false_positives():
    normals = np.array([0.1, 0.2, 0.15, 0.05, 0.3, 0.12, 0.08, 0.25, 0.18, 0.22])
    t = normal_fpr_threshold(normals, fpr_budget=0.1)
    assert (normals >= t).mean() <= 0.2   # ~≤10% of normals exceed it (quantile granularity)


def test_calibrate_improves_specificity_vs_default():
    rng = np.random.default_rng(0)
    n = 60
    y_pneu = np.array([1] * 40 + [0] * 20)
    y_norm = 1 - y_pneu
    # consolidation/lung_opacity separate the classes; others are noisy on normals.
    scores = {
        "consolidation": np.concatenate([rng.uniform(0.5, 0.9, 40), rng.uniform(0.1, 0.5, 20)]),
        "lung_opacity": np.concatenate([rng.uniform(0.5, 0.9, 40), rng.uniform(0.1, 0.5, 20)]),
        "pneumothorax": rng.uniform(0.0, 0.6, n),
        "pleural_effusion": rng.uniform(0.0, 0.6, n),
        "cardiomegaly": rng.uniform(0.0, 0.6, n),
    }
    abnormal = list(scores)
    thr = calibrate(scores, y_pneu, y_norm, signal_findings=["consolidation", "lung_opacity"],
                    critical_findings={"pneumothorax"}, target_sensitivity=0.9)
    default = {f: 0.5 for f in abnormal}
    base = triage_metrics(scores, default, y_pneu, y_norm, abnormal)
    cal = triage_metrics(scores, thr, y_pneu, y_norm, abnormal)
    assert cal["specificity"] >= base["specificity"]   # over-flagging reduced
    assert cal["sensitivity"] >= 0.85                  # recall preserved


def test_pneumothorax_threshold_is_capped_low():
    # even if normals score high on pneumothorax, the critical cap keeps it low.
    scores = {
        "consolidation": np.array([0.8, 0.7, 0.2, 0.1]),
        "lung_opacity": np.array([0.8, 0.7, 0.2, 0.1]),
        "pneumothorax": np.array([0.9, 0.9, 0.9, 0.9]),
        "pleural_effusion": np.array([0.1, 0.1, 0.1, 0.1]),
        "cardiomegaly": np.array([0.1, 0.1, 0.1, 0.1]),
    }
    y_pneu = np.array([1, 1, 0, 0])
    y_norm = 1 - y_pneu
    thr = calibrate(scores, y_pneu, y_norm, signal_findings=["consolidation", "lung_opacity"],
                    critical_findings={"pneumothorax"}, target_sensitivity=0.9, critical_cap=0.45)
    assert thr["pneumothorax"] <= 0.45
