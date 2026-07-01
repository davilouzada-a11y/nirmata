# Model Card — Radiografia AI (chest X-ray triage)

Following the *Model Cards for Model Reporting* framework (Mitchell et al., 2019).
This card describes the model **as integrated in this project**, and is
deliberately conservative about what has and hasn't been shown.

> ⚠️ **This is not a medical device and not a validated diagnostic.** It is a
> decision-support prototype whose output is advisory and requires mandatory
> review by a qualified radiologist. See [When NOT to use](#when-not-to-use).

---

## Model details

- **Purpose:** Multi-label triage of frontal chest radiographs, as the inference
  layer of a decision-support app with an enforced human-review workflow.
- **Backends (`ML_BACKEND`):**
  - `mock` (default) — deterministic pseudo-scores; no ML, for developing the app.
  - **`xrv`** — TorchXRayVision **DenseNet-121** (`densenet121-res224-all`),
    pretrained; **the backend these results describe**.
  - `torch` — a project-trained checkpoint (`ml/training`); **untrained here**.
- **Surfaced findings (6):** `normal_no_critical_finding`, `pneumothorax`
  (critical), `pleural_effusion`, `consolidation`, `lung_opacity`, `cardiomegaly`.
  The app maps these to TorchXRayVision pathologies and derives `normal` from the
  strongest abnormal signal.
- **Version string recorded per prediction:** `cxr-torchxrayvision-densenet121-res224-all`.
- **License/attribution:** TorchXRayVision (github.com/mlmed/torchxrayvision);
  weights trained by that project.

## Intended use

- **Primary:** research/education and an engineering reference for a
  human-in-the-loop CXR decision-support pipeline (de-identification, workflow,
  audit, mandatory review).
- **Users:** developers and researchers; in any clinical-adjacent setting, only a
  qualified radiologist acting as the mandatory reviewer.
- **Out of scope:** autonomous or primary diagnosis; unsupervised clinical use.

## Training data

The pretrained weights were trained by TorchXRayVision on a union of public
datasets: **NIH ChestX-ray14, CheXpert, MIMIC-CXR, PadChest, Google, OpenI,
Kaggle**. Labels there are largely NLP-derived from reports (noisy). This project
did **not** train the model.

## Evaluation data

- **Dataset:** covid-chestxray-dataset (public, GitHub), frontal X-rays only.
- **Sample:** n = 73 (56 pneumonia / 17 No-Finding).
- **Labels:** diagnosis-centric (pneumonia/COVID) used as a radiographic
  consolidation/opacity **proxy**; No-Finding = normal.
- ⚠️ **Overlap:** the pretrained model was trained on public data that overlaps
  the evaluation domain → results are **optimistic**, not an external validation.

## Metrics & quantitative results

Reported with bootstrap 95% CIs; calibration via 5-fold stratified CV. Full detail
in [`ml/validation/reports/VALIDATION_SUMMARY.md`](ml/validation/reports/VALIDATION_SUMMARY.md).

| What | Result |
| --- | --- |
| `consolidation` vs pneumonia | AUROC **0.79** (0.63–0.92) |
| `lung_opacity` vs pneumonia | AUROC **0.81** (0.65–0.93) |
| Abnormal-vs-normal **triage** | **sensitivity 0.95**, specificity 0.35 |
| Effect of adding `lung_opacity` | triage sensitivity 0.89 → 0.95 |
| Threshold calibration | **no specificity gain** (frontier ≤ ~0.42; ±0.3 variance) |

## Factors & subgroups

Not assessed. No analysis by sex, age, scanner, site, or acquisition — the
evaluation set is too small and unrepresentative. Frontal (PA/AP) views only.

## Ethical & safety considerations

- **Human oversight is enforced:** no study is finalized without a registered
  radiologist review; AI output is labeled advisory throughout the UI.
- **Privacy:** DICOM uploads are de-identified before storage (PHI removed/
  pseudonymized, UIDs regenerated); actions are audit-logged.
- **Bias/generalization:** unknown and unmeasured; the training data has known
  demographic and site skews.
- **Over-reliance risk:** low specificity means many false flags — reviewers must
  not treat a flag as confirmation, nor a "normal" as clearance.

## When NOT to use

Do **not** use this model / these weights:

- for **any real diagnostic or triage decision** without a qualified radiologist
  making the final call;
- as a **standalone/autonomous** diagnostic device, or to "clear" a study as normal;
- to rely on **`pneumothorax`, `pleural_effusion`, or `cardiomegaly`** outputs —
  these had **no validation labels** here and are effectively **unvalidated**
  (pneumothorax is critical and only kept at a conservative threshold);
- on inputs unlike the evaluated domain: **lateral views, pediatric, non-chest,
  CT, or non-radiograph** images;
- in a **new site/scanner/population** without local (re)validation and threshold
  recalibration;
- for any regulated clinical purpose — it is **not cleared by any regulator**
  (e.g., FDA/Anvisa) and this project makes no such claim.

## Caveats & recommendations

- Treat all numbers as **optimistic lower-effort estimates**, not clinical evidence.
- Before any clinical consideration: assemble a **local, adjudicated, well-powered**
  test set (≥ hundreds of cases *per finding*, ample clean normals), run
  `ml/validation/` for external validation, and recalibrate thresholds locally.
- Prioritize **sensitivity / low false-negative rate on critical findings**
  (pneumothorax) and report calibration + subgroup performance.
- Specificity is the current weak point; the evidence says the fix is
  **data + model**, not threshold tuning.
