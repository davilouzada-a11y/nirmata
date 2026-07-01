# Validation

Clinical validation of the inference backend on **real, labeled** chest X-rays,
with bootstrap 95% CIs. Reports AUROC / AUPRC / sensitivity / specificity — not
just accuracy — because missing a positive matters more than overall accuracy.

```
ml/validation/
├── metrics.py            # AUROC (+bootstrap CI), AUPRC, sens/spec/PPV/NPV
├── datasets/covid_cxr.py # fetches real CXRs from covid-chestxray-dataset (GitHub)
└── run_covid.py          # runs the xrv backend on it → JSON + Markdown report
reports/                  # committed validation reports
```

## Run

```bash
pip install torch torchvision torchxrayvision scikit-learn pandas pillow
python -m ml.validation.run_covid --limit-pos 60 --out ml/validation/reports
```

Downloads a capped sample of frontal radiographs, runs the pretrained model, and
writes `reports/covid_cxr_<date>.{json,md}`.

## What was validated (and what wasn't)

The reachable public dataset (covid-chestxray-dataset) is pneumonia/COVID-centric
with few normals, so it supports:

- **Pneumonia / consolidation detection** — AUROC of the model's consolidation /
  lung-opacity signal, positives = `Pneumonia*`, negatives = `No Finding`.
- **Abnormal-vs-normal triage** — does the app's `overall_status` flag pneumonia
  studies as abnormal at the real operating thresholds (the key safety property)?

It does **not** provide ground truth for pneumothorax / effusion / cardiomegaly.

## Honest caveats (read before trusting the numbers)

1. **Not a true external validation.** The pretrained model (TorchXRayVision) was
   trained on overlapping public data (NIH/CheXpert/MIMIC/PadChest/…), so these
   numbers are **optimistic**.
2. **Few normals** → wide confidence intervals; specificity is noisy.
3. **Label proxy.** The dataset's labels are diagnosis-centric (pneumonia/COVID);
   we use them as a radiographic consolidation/opacity proxy.
4. **HuggingFace is blocked in this environment**, so NIH/CheXpert/MIMIC couldn't
   be streamed here. The harness is CSV/predictor-agnostic — point it at a local
   NIH/CheXpert/MIMIC split for a proper, well-powered, truly-external validation.

## For a real (regulatory-grade) validation

- Use a **held-out local dataset** from your own site (true external test).
- Ensure ≥ a few hundred cases **per finding**, with radiologist-adjudicated labels.
- Report per-class sensitivity with **low FNR on critical findings** (pneumothorax),
  calibration, and subgroup performance — then calibrate thresholds locally.
