# Threshold calibration — 2026-07-01

**Model:** `torchxrayvision/densenet121-res224-all` · **Dataset:** covid-chestxray-dataset (public, GitHub) · n=73 (56 pneumonia, 17 normal)
**Target triage sensitivity:** ≥ 0.90 · **5-fold stratified CV** (calibrated on train, measured on held-out)

## Triage: abnormal-vs-normal (cross-validated)
| thresholds | sensitivity | specificity |
| --- | --- | --- |
| default (0.5) | 0.95 ± 0.04 | 0.35 ± 0.32 |
| **calibrated** | 0.93 ± 0.04 | **0.30 ± 0.27** |

## Sensitivity/specificity frontier (CV) — the achievable tradeoff
| target sens | achieved sens | specificity |
| --- | --- | --- |
| 0.80 | 0.89 | 0.42 ± 0.34 |
| 0.85 | 0.93 | 0.35 ± 0.32 |
| 0.90 | 0.93 | 0.30 ± 0.27 |
| 0.95 | 0.96 | 0.20 ± 0.27 |

## Recommended thresholds (calibrated on all data)
| finding | threshold |
| --- | --- |
| pneumothorax | 0.45 |
| pleural_effusion | 0.716 |
| consolidation | 0.163 |
| lung_opacity | 0.239 |
| cardiomegaly | 0.647 |

## Caveats
- Small sample (esp. normals) → noisy CV estimates.
- Pneumonia-proxy labels; only consolidation/lung_opacity have positives here.
- pneumothorax/effusion/cardiomegaly calibrated on normals only (specificity), recall uncalibrated — pneumothorax capped low to stay sensitive.
- Recalibrate on a local, well-powered, adjudicated dataset before clinical use.
