# Validation summary — Radiografia AI (xrv backend)

Consolidated results from the validation and calibration runs. Reproduce with
`python -m ml.validation.run_covid` and `python -m ml.validation.calibrate_covid`.

- **Model:** TorchXRayVision `densenet121-res224-all` (pretrained on NIH,
  CheXpert, MIMIC-CXR, PadChest, Google, OpenI, Kaggle).
- **App surface:** 6 findings — normal, pneumothorax*, pleural_effusion,
  consolidation, lung_opacity, cardiomegaly (*critical).
- **Validation data:** covid-chestxray-dataset (public, GitHub), frontal X-rays,
  **n=73** (56 pneumonia, 17 No-Finding). Bootstrap 95% CIs.
- **Date:** 2026-07-01.

## 1. Discrimination (real radiographs)

| Signal | AUROC (95% CI) | at op. threshold |
| --- | --- | --- |
| `consolidation` vs pneumonia | 0.79 (0.63–0.92) | sens 0.82 · spec 0.71 |
| `lung_opacity` vs pneumonia | 0.81 (0.65–0.93) | sens 0.82 · spec 0.76 |
| `normal` vs No-Finding | 0.78 (0.64–0.90) | sens 0.35 · spec 0.95 |

The model reads pathology from real images (AUROC ~0.8, clearly above chance).

## 2. Abnormal-vs-normal triage (the safety property)

| configuration | sensitivity | specificity |
| --- | --- | --- |
| 5 findings (before) | 0.89 | 0.35 |
| **6 findings (after `lung_opacity`)** | **0.95** | 0.35 |

Adding `lung_opacity` — motivated directly by §1 — cut missed pneumonias from
6 → 3 with no specificity cost. Validation drove a real product change.

## 3. Threshold calibration — did not help

5-fold stratified CV (calibrate on train, measure on held-out). Sens/spec
frontier:

| target sensitivity | specificity (CV) |
| --- | --- |
| 0.80 | 0.42 ± 0.34 |
| 0.90 | 0.30 ± 0.27 |
| 0.95 | 0.20 ± 0.27 |

Frontier is shallow and variance is huge (17 normals). **Thresholds are not the
lever;** the ceiling is model separability + a tiny, noisy normal set. No
recalibrated thresholds were shipped.

## 4. What was NOT validated

- **pneumothorax, pleural_effusion, cardiomegaly** — no positive ground truth in
  this dataset. Their behavior here is **unvalidated** (pneumothorax, being
  critical, is kept at a conservative low threshold).
- Any true **external** performance — the pretrained weights overlap the public
  training sets, so all numbers are **optimistic**, not external validation.

## 5. Bottom line

Genuine "reads chest X-rays" evidence for consolidation/opacity + a working,
sensitive pneumonia triage — but **not** a validated multi-finding diagnostic.
The blocking need is **data**: more clean normals and radiographic per-finding
labels, plus local recalibration, before any clinical consideration.
