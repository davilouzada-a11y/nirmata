"""Validate the real (xrv) backend on the covid-chestxray-dataset.

Reports, with bootstrap 95% CIs:
  * As shipped by the app — AUROC of the `consolidation` and `normal` scores, and
    the app's abnormal-vs-normal triage sensitivity/specificity at the real
    operating thresholds.
  * For context — AUROC of the underlying model's richer pneumonia signals
    (Lung Opacity / Pneumonia / Consolidation) that the 4-class app does NOT
    surface, to distinguish "model can't read RX" from "our class set is narrow".

    python -m ml.validation.run_covid --limit-pos 60 --out ml/validation/reports

Honest caveats (see README): few normals, pneumonia-centric labels, and the
pretrained model was trained on overlapping public data (optimistic, not a true
external validation).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date

import numpy as np

from ml.inference.xrv_predictor import get_xrv_predictor
from ml.validation.datasets import covid_cxr
from ml.validation.metrics import evaluate_score, binary_at_threshold

APP_CONSOLIDATION_THR = 0.50  # from XRV_DEFAULT_THRESHOLDS


def _fmt(m: dict) -> str:
    lo, hi = m["auroc_ci95"]
    return (f"AUROC {m['auroc']:.3f} (95% CI {lo:.3f}–{hi:.3f}) · "
            f"AUPRC {m['auprc']:.3f} · sens {m['sensitivity']:.2f} · spec {m['specificity']:.2f} "
            f"(n={m['n']}, pos={m['n_pos']}, neg={m['n_neg']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-pos", type=int, default=60)
    ap.add_argument("--limit-neg", type=int, default=None)
    ap.add_argument("--cache", default="ml/validation/.cache/covid")
    ap.add_argument("--out", default="ml/validation/reports")
    ap.add_argument("--weights", default="densenet121-res224-all")
    args = ap.parse_args()

    print("Loading real chest X-rays (covid-chestxray-dataset)…")
    samples = covid_cxr.load_samples(args.cache, limit_pos=args.limit_pos, limit_neg=args.limit_neg)
    print(f"  {len(samples)} images "
          f"({sum(s['labels']['pneumonia'] for s in samples)} pneumonia, "
          f"{sum(s['labels']['normal'] for s in samples)} normal)")

    predictor = get_xrv_predictor(args.weights)

    y_pneu, y_norm = [], []
    app_consolidation, app_lung_opacity, app_normal, app_abnormal_pred = [], [], [], []
    raw = {p: [] for p in ["Lung Opacity", "Pneumonia", "Consolidation"]}

    print("Running inference…")
    for i, s in enumerate(samples, 1):
        res = predictor.predict(s["image_path"])
        probs = {f["finding_code"]: f["probability"] for f in res["findings"]}
        abnormal = any(f["is_positive"] for f in res["findings"]
                       if f["finding_code"] != "normal_no_critical_finding")
        y_pneu.append(s["labels"]["pneumonia"])
        y_norm.append(s["labels"]["normal"])
        app_consolidation.append(probs["consolidation"])
        app_lung_opacity.append(probs.get("lung_opacity", float("nan")))
        app_normal.append(probs["normal_no_critical_finding"])
        app_abnormal_pred.append(1 if abnormal else 0)
        scores = predictor.raw_pathology_scores(s["image_path"])
        for p in raw:
            raw[p].append(scores.get(p, float("nan")))
        if i % 10 == 0:
            print(f"  {i}/{len(samples)}")

    y_pneu = np.array(y_pneu)
    y_norm = np.array(y_norm)

    # As shipped by the app.
    app_consolidation_m = evaluate_score(y_pneu, app_consolidation, APP_CONSOLIDATION_THR)
    app_lung_opacity_m = evaluate_score(y_pneu, app_lung_opacity, 0.50)
    app_normal_m = evaluate_score(y_norm, app_normal, 0.50)
    # App triage: does overall_status flag pneumonia as abnormal / normals as normal?
    triage = binary_at_threshold(y_pneu, np.array(app_abnormal_pred), 0.5)

    # Underlying model context.
    raw_m = {p: evaluate_score(y_pneu, raw[p], 0.5) for p in raw}

    report = {
        "generated": str(date.today()),
        "dataset": "covid-chestxray-dataset (public, GitHub)",
        "model": f"torchxrayvision/{args.weights}",
        "n_images": len(samples),
        "n_pneumonia": int(y_pneu.sum()),
        "n_normal": int(y_norm.sum()),
        "task": "pneumonia/consolidation vs No Finding (frontal X-rays)",
        "app_shipped": {
            "consolidation_score_vs_pneumonia": app_consolidation_m,
            "lung_opacity_score_vs_pneumonia": app_lung_opacity_m,
            "normal_score_vs_normal": app_normal_m,
            "triage_pneumonia_flagged_abnormal": triage,
        },
        "underlying_model_context": raw_m,
        "caveats": [
            "Few normal cases; wide CIs.",
            "Labels are diagnosis-centric (pneumonia/COVID), used as a consolidation proxy.",
            "Pretrained model trained on overlapping public data — optimistic, not a true external validation.",
            "No pneumothorax/effusion/cardiomegaly ground truth in this dataset.",
        ],
    }

    os.makedirs(args.out, exist_ok=True)
    stem = os.path.join(args.out, f"covid_cxr_{report['generated']}")
    with open(stem + ".json", "w") as fh:
        json.dump(report, fh, indent=2)

    md = [
        f"# Validation report — {report['generated']}",
        "",
        f"**Model:** `{report['model']}`  ·  **Dataset:** {report['dataset']}",
        f"**Task:** {report['task']}  ·  **n={report['n_images']}** "
        f"({report['n_pneumonia']} pneumonia, {report['n_normal']} normal)",
        "",
        "## As shipped by the app (real thresholds)",
        f"- **`consolidation` score vs pneumonia:** {_fmt(app_consolidation_m)}",
        f"- **`lung_opacity` score vs pneumonia:** {_fmt(app_lung_opacity_m)}",
        f"- **`normal` score vs No-Finding:** {_fmt(app_normal_m)}",
        f"- **Triage (pneumonia flagged abnormal):** sensitivity "
        f"{triage['sensitivity']:.2f}, specificity {triage['specificity']:.2f} "
        f"(TP={triage['tp']} FN={triage['fn']} TN={triage['tn']} FP={triage['fp']})",
        "",
        "## Underlying model — richer signals the app does NOT surface (context)",
    ]
    for p, m in raw_m.items():
        md.append(f"- **{p}:** {_fmt(m)}")
    md += ["", "## Caveats"] + [f"- {c}" for c in report["caveats"]]
    with open(stem + ".md", "w") as fh:
        fh.write("\n".join(md) + "\n")

    print("\n" + "\n".join(md))
    print(f"\nWrote {stem}.json / .md")


if __name__ == "__main__":
    main()
