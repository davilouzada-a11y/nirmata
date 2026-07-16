import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_reviewer
from app.core.db import get_db
from app.constants import DISCLAIMER
from app.models.study import Study
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.study import StudyOut, StudyListItem, StudyStateChangeRequest
from app.schemas.prediction import PredictionResponse, FindingOut
from app.schemas.review import ReviewCreate, ReviewOut
from app.services import audit_service, review_service, study_service

router = APIRouter()


def _get_study_or_404(db: Session, study_id: str) -> Study:
    study = db.query(Study).filter_by(id=study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return study


def _prediction_response(prediction: Prediction) -> PredictionResponse:
    findings = [
        FindingOut(
            finding_code=f.finding_code, probability=f.probability, threshold=f.threshold,
            is_positive=f.is_positive,
            heatmap_url=(
                f"/studies/{prediction.study_id}/heatmaps/{f.finding_code}"
                if f.heatmap_path else None
            ),
        )
        for f in prediction.findings
    ]
    return PredictionResponse(
        study_id=prediction.study_id, prediction_id=prediction.id,
        model_version=prediction.model_version.version,
        overall_status=prediction.overall_status,
        inference_time_ms=prediction.inference_time_ms,
        findings=findings, disclaimer=DISCLAIMER,
    )


@router.post("/upload", response_model=StudyOut, status_code=201)
def upload_study(
    patient_code: str = Form(...),
    view: str = Form("PA"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        study = study_service.create_study(
            db, patient_code=patient_code, view=view,
            filename=file.filename or "image.png", content=content, user_id=user.id,
        )
    except ValueError as err:
        # De-identification failed → reject the upload (never persist PHI).
        raise HTTPException(status_code=422, detail=str(err))
    return study


@router.get("", response_model=list[StudyListItem])
def list_studies(status: str | None = None, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return study_service.list_studies(db, status=status)


@router.get("/stats")
def study_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Operations/quality metrics (counts by state, AI/human divergence rate…)."""
    return study_service.stats(db)


@router.get("/{study_id}", response_model=StudyOut)
def get_study(study_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_study_or_404(db, study_id)


@router.get("/{study_id}/image")
def get_image(study_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    study = _get_study_or_404(db, study_id)
    if not study.image_path or not os.path.exists(study.image_path):
        raise HTTPException(status_code=404, detail="Image file missing")
    audit_service.log(
        db,
        user_id=user.id,
        action="image.viewed",
        entity="study",
        entity_id=study.id,
        payload={"image_format": study.image_format, "endpoint": "study.image"},
    )
    db.commit()
    return FileResponse(study.image_path)


@router.post("/{study_id}/predict", response_model=PredictionResponse)
def predict(study_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    study = _get_study_or_404(db, study_id)
    prediction = study_service.run_prediction(db, study, user_id=user.id)
    return _prediction_response(prediction)


@router.post("/{study_id}/hold", response_model=StudyOut)
def hold_study(study_id: str, payload: StudyStateChangeRequest,
               db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    study = _get_study_or_404(db, study_id)
    if study.status == "finalized":
        raise HTTPException(status_code=409, detail="Finalized studies cannot be put on hold.")
    if study.status == "blocked":
        raise HTTPException(status_code=409, detail="Study is already on hold.")
    previous_status = study.status
    study.status = "blocked"
    audit_service.log(
        db,
        user_id=user.id,
        action="study.hold",
        entity="study",
        entity_id=study.id,
        payload={
            "previous_status": previous_status,
            "new_status": study.status,
            "reason": payload.reason,
        },
    )
    db.commit()
    db.refresh(study)
    return study


@router.post("/{study_id}/reopen", response_model=StudyOut)
def reopen_study(study_id: str, payload: StudyStateChangeRequest,
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    study = _get_study_or_404(db, study_id)
    if study.status != "blocked":
        raise HTTPException(status_code=409, detail="Only blocked studies can be reopened.")
    previous_status = study.status
    prediction = study_service.latest_prediction(db, study.id)
    study.status = "predicted" if prediction else "uploaded"
    audit_service.log(
        db,
        user_id=user.id,
        action="study.reopened",
        entity="study",
        entity_id=study.id,
        payload={
            "previous_status": previous_status,
            "new_status": study.status,
            "reason": payload.reason,
            "prediction_id": prediction.id if prediction else None,
        },
    )
    db.commit()
    db.refresh(study)
    return study


@router.get("/{study_id}/prediction", response_model=PredictionResponse)
def get_prediction(study_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_study_or_404(db, study_id)
    prediction = study_service.latest_prediction(db, study_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction yet for this study")
    return _prediction_response(prediction)


@router.get("/{study_id}/heatmaps/{finding_code}")
def get_heatmap(study_id: str, finding_code: str, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    prediction = study_service.latest_prediction(db, study_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="No prediction yet")
    finding = next((f for f in prediction.findings if f.finding_code == finding_code), None)
    if not finding or not finding.heatmap_path or not os.path.exists(finding.heatmap_path):
        raise HTTPException(status_code=404, detail="No heatmap for this finding")
    audit_service.log(
        db,
        user_id=user.id,
        action="image.heatmap_viewed",
        entity="study",
        entity_id=study_id,
        payload={"finding_code": finding_code, "endpoint": "study.heatmap"},
    )
    db.commit()
    return FileResponse(finding.heatmap_path, media_type="image/png")


@router.post("/{study_id}/review", response_model=ReviewOut, status_code=201)
def create_review(study_id: str, payload: ReviewCreate, db: Session = Depends(get_db),
                  reviewer: User = Depends(require_reviewer)):
    study = _get_study_or_404(db, study_id)
    return review_service.create_review(db, study, payload, reviewer_id=reviewer.id)


@router.get("/{study_id}/review", response_model=ReviewOut)
def get_review(study_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review = review_service.get_review(db, study_id)
    if not review:
        raise HTTPException(status_code=404, detail="No review for this study")
    return review
