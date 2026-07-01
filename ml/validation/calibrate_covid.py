"""Calibrate the app's decision thresholds on real X-rays and report the
honest, cross-validated effect on abnormal-vs-normal triage.

Method (avoids tuning-on-test circularity):
  * Run the model once to get per-finding scores for every image.
  * Stratified k-fold CV: on each training split, calibrate thresholds; evaluate
    triage on the held-out split with (a) default 0.5 thresholds and (b) the
    calibrated thresholds. Aggregate across folds → honest before/after.
  * Also emit thresholds calibrated on ALL data (the recommended set to ship).

    python -m ml.validation.calibrate_covid --limit-pos 60 --out ml/validation/reports

Same caveats as the validation run: few normals, pneumonia-proxy labels,
pretrained-weights overlap. Treat as a demonstration + starting point; recalibrate
on a local, well-powered dataset before clinical use.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date

import numpy as np

from ml.inference.xrv_predictor import get_xrv_predictor
from ml.validation.datasets import covid_cxr
from ml.validation.calibrate import calibrate, triage_metrics

ABNORMAL = ["pneumothorax", "pleural_effusion", "consolidation", "lung_opacity", "cardiomegaly"]
SIGNAL = ["consolidation", "lung_opacity"]      # have pneumonia positives here
CRITICAL = {"pneumothorax"}
DEFAULT_THR = {f: 0.5 for f in ABNORMAL}


def _collect_scores(samples, weights):
    predictor = get_xrv_predictor(weights)
    scores = {f: [] for f in ABNORMAL}
    y_pneu, y_norm = [], []
    for i, s in enumerate(samples, 1):
        res = predictor.predict(s["image_path"])
        probs = {f["finding_code"]: f["probability"] for f in res["findings"]}
        for f in ABNORMAL:
            scores[f].append(probs.get(f, 0.0))
        y_pneu.append(s["labels"]["pneumonia"])
        y_norm.append(s["labels"]["normal"])
        if i % 10 == 0:
            print(f"  {i}/{len(samples)}")
    scores = {f: np.array(v) for f, v in scores.items()}
    return scores, np.array(y_pneu), np.array(y_norm)


def _subset(scores, idx):
    return {f: v[idx] for f, v in scores.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-pos", type=int, default=60)
    ap.add_argument("--cache", default="ml/validation/.cache/covid")
    ap.add_argument("--out", default="ml/validation/reports")
    ap.add_argument("--weights", default="densenet121-res224-all")
    ap.add_argument("--target-sensitivity", type=float, default=0.90)
    ap.add_argument("--folds", type=int, default=5)
    args = ap.parse_args()

    from sklearn.model_selection import StratifiedKFold

    print("Loading real chest X-rays…")
    samples = covid_cxr.load_samples(args.cache, limit_pos=args.limit_pos)
    print(f"  {len(samples)} images")
    print("Scoring with the model…")
    scores, y_pneu, y_norm = _collect_scores(samples, args.weights)

    skf = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=0)
    splits = list(skf.split(np.zeros(len(y_pneu)), y_pneu))

    def _agg(rows, key):
        vals = [r[key] for r in rows if not np.isnan(r[key])]
        return {"mean": float(np.mean(vals)), "std": float(np.std(vals))}

    def _cv_at(target: float):
        rows = []
        for train_idx, test_idx in splits:
            thr = calibrate(_subset(scores, train_idx), y_pneu[train_idx], y_norm[train_idx],
                            signal_findings=SIGNAL, critical_findings=CRITICAL,
                            target_sensitivity=target)
            te = _subset(scores, test_idx)
            rows.append(triage_metrics(te, thr, y_pneu[test_idx], y_norm[test_idx], ABNORMAL))
        return {"sensitivity": _agg(rows, "sensitivity"), "specificity": _agg(rows, "specificity")}

    # ---- Cross-validated before/after at the requested target -------------
    before = [triage_metrics(_subset(scores, te), DEFAULT_THR, y_pneu[te], y_norm[te], ABNORMAL)
              for _, te in splits]
    cv = {
        "default_thresholds": {"sensitivity": _agg(before, "sensitivity"),
                               "specificity": _agg(before, "specificity")},
        "calibrated_thresholds": _cv_at(args.target_sensitivity),
    }

    # ---- Sensitivity/specificity frontier (why thresholds alone can't win) -
    frontier = {f"{t:.2f}": _cv_at(t) for t in (0.80, 0.85, 0.90, 0.95)}

    # ---- Recommended thresholds (calibrated on ALL data) ------------------
    recommended = calibrate(scores, y_pneu, y_norm, signal_findings=SIGNAL,
                            critical_findings=CRITICAL, target_sensitivity=args.target_sensitivity)
    recommended = {f: round(t, 3) for f, t in recommended.items()}

    report = {
        "generated": str(date.today()),
        "dataset": "covid-chestxray-dataset (public, GitHub)",
        "model": f"torchxrayvision/{args.weights}",
        "n_images": len(samples), "n_pneumonia": int(y_pneu.sum()), "n_normal": int(y_norm.sum()),
        "target_sensitivity": args.target_sensitivity, "folds": args.folds,
        "cv_triage": cv,
        "sens_spec_frontier": frontier,
        "recommended_thresholds": recommended,
        "caveats": [
            "Small sample (esp. normals) → noisy CV estimates.",
            "Pneumonia-proxy labels; only consolidation/lung_opacity have positives here.",
            "pneumothorax/effusion/cardiomegaly calibrated on normals only (specificity), "
            "recall uncalibrated — pneumothorax capped low to stay sensitive.",
            "Recalibrate on a local, well-powered, adjudicated dataset before clinical use.",
        ],
    }

    os.makedirs(args.out, exist_ok=True)
    stem = os.path.join(args.out, f"calibration_{report['generated']}")
    with open(stem + ".json", "w") as fh:
        json.dump(report, fh, indent=2)

    b, a = cv["default_thresholds"], cv["calibrated_thresholds"]
    md = [
        f"# Threshold calibration — {report['generated']}",
        "",
        f"**Model:** `{report['model']}` · **Dataset:** {report['dataset']} · "
        f"n={report['n_images']} ({report['n_pneumonia']} pneumonia, {report['n_normal']} normal)",
        f"**Target triage sensitivity:** ≥ {args.target_sensitivity:.2f} · "
        f"**{args.folds}-fold stratified CV** (calibrated on train, measured on held-out)",
        "",
        "## Triage: abnormal-vs-normal (cross-validated)",
        "| thresholds | sensitivity | specificity |",
        "| --- | --- | --- |",
        f"| default (0.5) | {b['sensitivity']['mean']:.2f} ± {b['sensitivity']['std']:.2f} "
        f"| {b['specificity']['mean']:.2f} ± {b['specificity']['std']:.2f} |",
        f"| **calibrated** | {a['sensitivity']['mean']:.2f} ± {a['sensitivity']['std']:.2f} "
        f"| **{a['specificity']['mean']:.2f} ± {a['specificity']['std']:.2f}** |",
        "",
        "## Sensitivity/specificity frontier (CV) — the achievable tradeoff",
        "| target sens | achieved sens | specificity |",
        "| --- | --- | --- |",
    ]
    for t, m in frontier.items():
        md.append(f"| {t} | {m['sensitivity']['mean']:.2f} | {m['specificity']['mean']:.2f} ± {m['specificity']['std']:.2f} |")
    md += [
        "",
        "## Recommended thresholds (calibrated on all data)",
        "| finding | threshold |",
        "| --- | --- |",
    ]
    md += [f"| {f} | {t} |" for f, t in recommended.items()]
    md += ["", "## Caveats"] + [f"- {c}" for c in report["caveats"]]
    with open(stem + ".md", "w") as fh:
        fh.write("\n".join(md) + "\n")

    print("\n" + "\n".join(md))
    print(f"\nWrote {stem}.json / .md")


if __name__ == "__main__":
    main()
