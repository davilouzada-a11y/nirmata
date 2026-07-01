# ML — Chest X-ray multi-label classifier

PyTorch training + inference for the five MVP findings:
`normal_no_critical_finding`, `pneumothorax`, `pleural_effusion`,
`consolidation`, `cardiomegaly`.

```
ml/
├── preprocessing/      # DICOM de-identification (PHI removal) + windowing — see its README
│   ├── deident.py      # PHI removal (PS3.15 basic confidentiality profile subset)
│   ├── windowing.py    # Modality/VOI LUT → 8-bit display
│   ├── transforms.py   # MONAI transforms (+augmentation) with numpy fallback
│   ├── pipeline.py     # process_dicom() / process_directory()
│   └── synthetic.py    # synthetic DICOMs with fake PHI (tests/demos)
├── training/
│   ├── config.yaml     # data paths, backbone, thresholds
│   ├── dataset.py      # ChestXrayDataset (CSV labels → tensors)
│   ├── train.py        # DenseNet-121, weighted BCE, AdamW+cosine, best-AUROC ckpt
│   └── evaluate.py     # per-class AUROC/AUPRC/sensitivity/specificity/F1/FNR
└── inference/
    ├── preprocess.py     # PNG/JPG/DICOM → normalized tensor
    ├── gradcam.py        # Grad-CAM heatmaps (explainability)
    ├── predictor.py      # our own checkpoint → findings + heatmaps
    └── xrv_predictor.py  # TorchXRayVision pretrained model (ML_BACKEND=xrv) — real CXR reading
```

## Read real X-rays now (no training)

`ML_BACKEND=xrv` uses [TorchXRayVision](https://github.com/mlmed/torchxrayvision)
DenseNet-121 pretrained on ~1M chest radiographs — genuine probabilities for
pneumothorax / effusion / consolidation / cardiomegaly, on CPU, no training:

```bash
pip install torch torchvision torchxrayvision
ML_BACKEND=xrv uvicorn app.main:app --reload   # from backend/
```

Still advisory (domain shift, not locally calibrated) — human review stays.

## Train

```bash
pip install -r ml/requirements.txt
# Prepare data/images/*.png and data/labels.csv (see column format in dataset.py)
python -m ml.training.train --config ml/training/config.yaml
python -m ml.training.evaluate --config ml/training/config.yaml \
    --checkpoint ml/training/checkpoints/cxr-densenet-v0.1.0.pt --split test
```

## Serve through the API

Point the backend at a trained checkpoint and switch the backend on:

```bash
export ML_BACKEND=torch
export MODEL_CHECKPOINT=./ml/inference/checkpoints/cxr-densenet-v0.1.0.pt
```

The backend's `InferenceService` imports `ml.inference.predictor.Predictor`
lazily, so torch is only required when `ML_BACKEND=torch`. The default `mock`
backend needs no ML dependencies.

## Data & governance notes

- Suggested datasets: **NIH ChestX-ray14** (volume) and **PadChest** (diversity,
  multi-label). Use de-identified images only.
- Two-reader labeling with third-reader adjudication is recommended; keep a
  written annotation manual with diagnostic criteria per finding.
- Validate on an **external** set (different hospital/scanner/population) before
  any clinical pilot. Prioritize **sensitivity / low FNR on critical findings**
  (e.g. pneumothorax) over headline accuracy.
- Grad-CAM is an interpretability aid, not diagnostic proof.
