"""Study lifecycle + inference persistence, enforcing the clinical workflow.

State machine:  uploaded → processing → predicted → under_review → reviewed → finalized

Rules enforced here and in review_service:
  * A study cannot be finalized without a registered human review.
  * Re-running inference creates a NEW prediction (never overwrites).
  * Every prediction records the exact model version used.
"""
from __future__ import annotations

import os

from sqlalchemy.orm import Session

from app.constants import (
    DEFAULT_THRESHOLDS,
    XRV_DEFAULT_THRESHOLDS,
)
from app.core.config import get_settings
from app.models.study import Study
from app.models.patient import Patient
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction, PredictionFinding
from app.services.inference_service import InferenceService
from app.services import audit_service
from app.services.clinical_policy import priority_for_overall

settings = get_settings()


def _storage(*parts: str) -> str:
    return os.path.join(settings.storage_dir, *parts)


def _deidentify_dicom(content: bytes):
    """Strip PHI from an uploaded DICOM before it is ever written to disk.

    Returns (clean_dicom_bytes, deident_summary, width, height). Raises
    ValueError if the file can't be parsed/de-identified, so the caller can
    reject the upload rather than risk persisting PHI.
    """
    from app.ml_bridge import ensure_ml_importable

    if not ensure_ml_importable():
        raise ValueError("De-identificação indisponível (pydicom/ml não instalado).")
    try:
        from ml.preprocessing.pipeline import process_dicom

        res = process_dicom(content, salt=settings.deident_salt, want_png=False, want_dicom=True)
    except Exception as err:  # malformed DICOM, decode error, etc.
        raise ValueError(f"Falha ao ler/de-identificar DICOM: {err}") from err
    return res.dicom_bytes, res.deident, res.width, res.height


def _active_model_spec() -> dict:
    """The model version + thresholds implied by the configured ML backend."""
    if settings.ml_backend == "xrv":
        return {
            "name": "Chest X-ray classifier (TorchXRayVision DenseNet-121)",
            "version": f"cxr-torchxrayvision-{settings.xrv_weights}",
            "training_dataset": "NIH, CheXpert, MIMIC-CXR, PadChest, Google, OpenI, Kaggle (pretrained)",
            "thresholds": XRV_DEFAULT_THRESHOLDS,
        }
    return {
        "name": "Chest X-ray multi-label classifier",
        "version": settings.model_version_name,
        "training_dataset": "NIH ChestX-ray14 + local review (MVP)",
        "thresholds": DEFAULT_THRESHOLDS,
    }


def get_or_create_model_version(db: Session) -> ModelVersion:
    spec = _active_model_spec()
    mv = db.query(ModelVersion).filter_by(version=spec["version"]).first()
    if mv:
        return mv
    mv = ModelVersion(
        name=spec["name"],
        version=spec["version"],
        training_dataset=spec["training_dataset"],
        threshold_config=spec["thresholds"],
    )
    db.add(mv)
    db.flush()
    return mv


def create_study(db: Session, *, patient_code: str, view: str, filename: str,
                 content: bytes, user_id: str | None) -> Study:
    """Persist an uploaded image and create a study in the `uploaded` state."""
    fmt = (os.path.splitext(filename)[1].lstrip(".") or "png").lower()
    if fmt in {"dcm", "dicom"}:
        fmt = "dicom"

    # De-identify DICOM uploads BEFORE anything touches disk.
    deident_summary = None
    width = height = None
    if fmt == "dicom":
        content, deident_summary, width, height = _deidentify_dicom(content)

    patient = Patient(external_code=patient_code, anonymized_flag=True)
    db.add(patient)
    db.flush()

    study = Study(
        patient_id=patient.id, patient_code=patient_code, view=view.upper(),
        status="uploaded", image_format=fmt, image_path="", width=width, height=height,
    )
    db.add(study)
    db.flush()

    dest = _storage("studies", study.id, f"image.{fmt}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(content)
    study.image_path = dest

    audit_service.log(db, user_id=user_id, action="study.upload", entity="study",
                      entity_id=study.id, payload={"patient_code": patient_code, "format": fmt})
    if deident_summary:
        audit_service.log(db, user_id=user_id, action="study.deidentify", entity="study",
                          entity_id=study.id, payload=deident_summary)
    db.commit()
    db.refresh(study)
    return study


def run_prediction(db: Session, study: Study, *, user_id: str | None) -> Prediction:
    """Run inference and persist a new Prediction (+ findings + heatmaps)."""
    mv = get_or_create_model_version(db)
    thresholds = mv.threshold_config or DEFAULT_THRESHOLDS

    study.status = "processing"
    db.flush()

    engine = InferenceService()
    result = engine.run(
        study.image_path, thresholds=thresholds,
        heatmap_dir=_storage("heatmaps"), study_id=study.id,
    )

    prediction = Prediction(
        study_id=study.id, model_version_id=mv.id,
        overall_status=result["overall_status"],
        inference_time_ms=result["inference_time_ms"],
    )
    db.add(prediction)
    db.flush()

    for f in result["findings"]:
        db.add(PredictionFinding(
            prediction_id=prediction.id, finding_code=f["finding_code"],
            probability=f["probability"], threshold=f["threshold"],
            is_positive=f["is_positive"], heatmap_path=f.get("heatmap_path"),
        ))

    study.status = "predicted"
    audit_service.log(db, user_id=user_id, action="study.predict", entity="study",
                      entity_id=study.id,
                      payload={"prediction_id": prediction.id,
                               "overall_status": prediction.overall_status,
                               "model_version": mv.version})
    db.commit()
    db.refresh(prediction)
    return prediction


def latest_prediction(db: Session, study_id: str) -> Prediction | None:
    return (
        db.query(Prediction)
        .filter_by(study_id=study_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )


def stats(db: Session) -> dict:
    """Aggregate metrics for an operations/quality dashboard."""
    from app.models.review import Review, ReviewFinding

    studies = db.query(Study).all()
    by_status: dict[str, int] = {}
    for s in studies:
        by_status[s.status] = by_status.get(s.status, 0) + 1

    by_overall: dict[str, int] = {}
    inf_times: list[int] = []
    for study in studies:
        pred = latest_prediction(db, study.id)
        if pred:
            by_overall[pred.overall_status] = by_overall.get(pred.overall_status, 0) + 1
            inf_times.append(pred.inference_time_ms)

    total_reviews = db.query(Review).count()
    reviews_with_divergence = (
        db.query(ReviewFinding.review_id)
        .filter(ReviewFinding.diverged_from_ai.is_(True))
        .distinct()
        .count()
    )
    divergence_rate = (reviews_with_divergence / total_reviews) if total_reviews else 0.0

    return {
        "total_studies": len(studies),
        "by_status": by_status,
        "by_overall_status": by_overall,
        "total_reviews": total_reviews,
        "reviews_with_divergence": reviews_with_divergence,
        "divergence_rate": round(divergence_rate, 4),
        "mean_inference_time_ms": round(sum(inf_times) / len(inf_times)) if inf_times else 0,
    }


def list_studies(db: Session, status: str | None = None) -> list[dict]:
    """Return queue rows with derived read priority (critical first)."""
    q = db.query(Study).order_by(Study.created_at.desc())
    if status:
        q = q.filter(Study.status == status)
    rows = []
    for study in q.all():
        pred = latest_prediction(db, study.id)
        overall = pred.overall_status if pred else None
        priority = priority_for_overall(overall)
        rows.append({
            "id": study.id, "patient_code": study.patient_code, "view": study.view,
            "status": study.status, "created_at": study.created_at,
            "overall_status": overall, "priority": priority,
        })
    # Critical studies bubble to the top of the worklist.
    rows.sort(key=lambda r: (r["priority"] != "critical", ))
    return rows
