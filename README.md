# Radiografia AI

A clinical **decision-support** web app for chest X-ray (CXR) triage: upload a
radiograph, get per-finding AI probabilities with Grad-CAM heatmaps, and finalize
only through a **mandatory human (radiologist) review**. Built from the blueprint
in the project brief.

> ⚠️ **Não é um dispositivo diagnóstico.** A IA é apoio à decisão; o laudo final é
> sempre de responsabilidade do médico. Uso assistencial real exige validação
> clínica e regularização (Anvisa) e segue a governança da CFM 2.454/2026.

## Architecture

```
[ Next.js frontend ]  upload · viewer · heatmap · findings · revisão médica
        │ REST
[ FastAPI backend ]   auth · estudos · orquestração de inferência · auditoria · workflow
        │
[ ML service (PyTorch) ]  preprocess · DenseNet-121 multirrótulo · Grad-CAM · thresholds
        │
[ PostgreSQL ] + [ object storage ]
```

The five MVP findings: `normal_no_critical_finding`, `pneumothorax`,
`pleural_effusion`, `consolidation`, `cardiomegaly` (pneumothorax = critical →
priority read).

```
.
├── docker-compose.yml      # db + backend + frontend
├── backend/                # FastAPI (runnable now; SQLite default, Postgres in compose)
│   └── app/{core,models,schemas,api,services}
├── frontend/               # Next.js App Router + Tailwind
│   └── app/{login,studies/[id],components,lib}
└── ml/                     # preprocessing (DICOM de-id) + training + inference
```

## Run it

### Option A — full stack with Docker

```bash
cp .env.example .env
docker compose up --build
# frontend → http://localhost:3000   backend docs → http://localhost:8000/docs
# seed login → radiologista@example.com / changeme123
```

### Option B — backend only, no infra (SQLite + mock inference)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head               # apply schema migrations
python -m app.demo                 # seed radiologist + 6 demo studies (synthetic CXRs)
uvicorn app.main:app --reload      # http://localhost:8000/docs
pytest                             # full-workflow test suite (7 tests)
```

`python -m app.demo` populates the worklist with procedurally-generated
chest-X-ray-like images in mixed workflow states (uploaded / predicted /
finalized) so the UI is immediately clickable. Use `python -m app.seed` instead
if you want an empty database with just the seed user + model version.

### Inference backends (`ML_BACKEND`)

| Value | What it is | Deps |
| --- | --- | --- |
| `mock` (default) | Deterministic pseudo-probabilities + generated heatmaps. Runs the whole clinical workflow with **no ML deps** — for developing the app itself. | none |
| `xrv` | **Reads the X-ray for real**: TorchXRayVision DenseNet-121 pretrained on ~1M chest radiographs (NIH, CheXpert, MIMIC-CXR, PadChest, …). Genuine probabilities for pneumothorax / effusion / consolidation / cardiomegaly. CPU-capable, no training. | `torch`, `torchxrayvision` |
| `torch` | Our own checkpoint trained via `ml/training`. | `torch` + a checkpoint |

```bash
# Read real chest X-rays with a pretrained model:
pip install torch torchvision torchxrayvision
ML_BACKEND=xrv uvicorn app.main:app --reload
```

> ⚠️ Even `xrv` is **advisory, not a certified diagnosis** — pretrained weights
> carry domain shift and aren't locally calibrated; mandatory human review stays.

## Clinical workflow (enforced by the backend)

```
uploaded → processing → predicted → under_review → reviewed → finalized
```

- **DICOM uploads are de-identified before they touch disk.** Every `.dcm` is
  run through `ml/preprocessing` (PHI tags removed/pseudonymized, UIDs
  regenerated, private/overlay groups stripped); a bad file is rejected with 422
  and the de-identification is logged to the audit trail. See
  [`ml/preprocessing/README.md`](ml/preprocessing/README.md).
- **No study is finalized without a registered human review.**
- Re-running inference creates a **new** prediction; old ones are never overwritten.
- Every prediction records the exact **model version**; every review records which
  prediction (and model) it acted on.
- **AI-vs-human divergence** is computed and persisted per finding.
- Every action (upload / predict / review) is written to an **audit trail**.

## API (selected)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/login` · `/auth/login/json` | obtain JWT |
| GET  | `/auth/me` | current user |
| POST | `/studies/upload` | upload a CXR (multipart) |
| GET  | `/studies` | worklist (critical first) |
| GET  | `/studies/stats` | ops/quality metrics (states, divergence rate, mean latency) |
| GET  | `/studies/{id}` · `/studies/{id}/image` | study + image |
| POST | `/studies/{id}/predict` | run inference (new prediction) |
| GET  | `/studies/{id}/prediction` | latest prediction |
| GET  | `/studies/{id}/heatmaps/{finding_code}` | Grad-CAM overlay PNG |
| POST | `/studies/{id}/review` | mandatory review → finalize |
| GET  | `/studies/{id}/review` | review record |
| GET  | `/audit/studies/{id}` | audit trail |
| GET  | `/models/versions` | model registry |

Sample prediction response:

```json
{
  "study_id": "…", "prediction_id": "…", "model_version": "cxr-densenet-v0.1.0",
  "overall_status": "abnormal_noncritical", "inference_time_ms": 842,
  "findings": [
    {"finding_code": "pleural_effusion", "probability": 0.91, "threshold": 0.62,
     "is_positive": true, "heatmap_url": "/studies/…/heatmaps/pleural_effusion"}
  ],
  "disclaimer": "Resultado automatizado sujeito à revisão médica obrigatória."
}
```

## Database migrations

Schema is versioned with **Alembic** (`backend/migrations/`). The Docker backend
runs `alembic upgrade head` on startup. To create a new migration after changing
a model:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

`init_db()` (create-all) remains as a convenience for local SQLite/tests; Alembic
is the source of truth for real deployments.

## Frontend notes

- The worklist shows live metrics (`StatsPanel`) and a **model registry** page
  (`/models`) listing each version and its per-finding thresholds.
- `DicomViewer` renders PNG/JPG directly and true **DICOM via DWV**
  (lazy-loaded), with the Grad-CAM heatmap as an opacity-controlled overlay.

## CI

`.github/workflows/radiografia-ci.yml` runs on every push / PR: backend
migration round-trip + pytest, the ML de-identification tests, and a frontend
production build.

## Governance / safety notes

- De-identified images for training; role-based access; audit logging; model
  versioning; separate research vs. production environments; a clear
  “apoio à decisão” banner — all reflected in the schema and UI.
- Evaluate with **sensitivity / low FNR on critical findings**, not headline
  accuracy; validate on an external set before any pilot (`ml/training/evaluate.py`).

See `backend/`, `frontend/`, and `ml/` for layer-specific details.
