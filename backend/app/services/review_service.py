"""Human review = the gate that finalizes a study.

No prediction becomes a final result without this step. AI-vs-human divergence
is computed and persisted per finding, and the model version under review is
preserved for traceability.
"""
from __future__ import annotations

from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models.study import Study
from app.models.prediction import Prediction
from app.models.review import Review, ReviewFinding
from app.schemas.review import ReviewCreate
from app.services import audit_service
from app.services.clinical_policy import active_policy
from app.services.study_service import latest_prediction


def create_review(db: Session, study: Study, payload: ReviewCreate, reviewer_id: str) -> Review:
    if study.status not in {"predicted", "under_review"}:
        audit_service.log(
            db,
            user_id=reviewer_id,
            action="policy.denied",
            entity="study",
            entity_id=study.id,
            payload={
                "reason": "invalid_review_state",
                "current_state": study.status,
                "required_states": ["predicted", "under_review"],
            },
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail=f"Study must be predicted before review (current state: {study.status}).",
        )

    # Resolve the prediction the reviewer acted on.
    if payload.prediction_id:
        prediction = db.query(Prediction).filter_by(
            id=payload.prediction_id, study_id=study.id
        ).first()
        if not prediction:
            audit_service.log(
                db,
                user_id=reviewer_id,
                action="policy.denied",
                entity="study",
                entity_id=study.id,
                payload={"reason": "prediction_id_not_found", "prediction_id": payload.prediction_id},
            )
            db.commit()
            raise HTTPException(status_code=404, detail="prediction_id not found for this study")
    else:
        prediction = latest_prediction(db, study.id)
    if not prediction:
        audit_service.log(
            db,
            user_id=reviewer_id,
            action="policy.denied",
            entity="study",
            entity_id=study.id,
            payload={"reason": "missing_prediction"},
        )
        db.commit()
        raise HTTPException(status_code=409, detail="No prediction exists to review.")

    policy = active_policy(db)
    audit_service.log(
        db,
        user_id=reviewer_id,
        action="policy.evaluated",
        entity="study",
        entity_id=study.id,
        payload={
            "clinical_policy_version": policy["version"],
            "policy_status": policy["status"],
            "prediction_id": prediction.id,
            "review_gate": "human_review_required",
            "allowed": True,
        },
    )
    ai_positive = {f.finding_code: f.is_positive for f in prediction.findings}

    review = Review(
        study_id=study.id, prediction_id=prediction.id, reviewer_id=reviewer_id,
        decision=payload.decision, final_report=payload.final_report,
        clinical_policy_version=policy["version"],
    )
    db.add(review)
    db.flush()

    divergences = []
    for f in payload.final_findings:
        diverged = ai_positive.get(f.finding_code) != f.final_label
        if diverged:
            divergences.append(f.finding_code)
        db.add(ReviewFinding(
            review_id=review.id, finding_code=f.finding_code,
            final_label=f.final_label, diverged_from_ai=diverged, comment=f.comment,
        ))

    # Reaching a registered review finalizes the study.
    study.status = "finalized"

    audit_service.log(db, user_id=reviewer_id, action="study.review", entity="study",
                      entity_id=study.id,
                      payload={"review_id": review.id, "decision": payload.decision,
                               "prediction_id": prediction.id,
                               "model_version_id": prediction.model_version_id,
                               "clinical_policy_version": policy["version"],
                               "divergences": divergences})
    db.commit()
    db.refresh(review)
    return review


def get_review(db: Session, study_id: str) -> Review | None:
    return (
        db.query(Review)
        .filter_by(study_id=study_id)
        .order_by(Review.reviewed_at.desc())
        .first()
    )
