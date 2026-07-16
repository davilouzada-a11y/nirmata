from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.models.review import Review, ReviewFinding
from app.models.user import User

router = APIRouter()


def _empty_bucket() -> dict:
    return {"reviewed_findings": 0, "divergences": 0, "divergence_rate": 0.0}


def _rate(divergences: int, total: int) -> float:
    return round(divergences / total, 4) if total else 0.0


@router.get("/divergence")
def get_divergence_report(
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
    model_version: str | None = Query(default=None),
    clinical_policy_version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Summarize AI-vs-human divergence for clinical governance.

    This endpoint reads persisted human review findings. It does not re-run AI
    inference or reinterpret cases; it reports where reviewers disagreed with
    the model output already stored at review time.
    """
    query = (
        db.query(ReviewFinding, Review, Prediction, ModelVersion)
        .join(Review, ReviewFinding.review_id == Review.id)
        .outerjoin(Prediction, Review.prediction_id == Prediction.id)
        .outerjoin(ModelVersion, Prediction.model_version_id == ModelVersion.id)
    )
    if date_from:
        query = query.filter(Review.reviewed_at >= date_from)
    if date_to:
        query = query.filter(Review.reviewed_at <= date_to)
    if model_version:
        query = query.filter(ModelVersion.version == model_version)
    if clinical_policy_version:
        if clinical_policy_version == "unknown_policy":
            query = query.filter(Review.clinical_policy_version.is_(None))
        else:
            query = query.filter(Review.clinical_policy_version == clinical_policy_version)

    rows = query.all()

    total_findings = len(rows)
    total_divergences = 0
    reviewed_study_ids = set()
    review_ids = set()
    decisions: dict[str, int] = defaultdict(int)
    by_finding: dict[str, dict] = defaultdict(_empty_bucket)
    by_model: dict[str, dict] = defaultdict(_empty_bucket)
    by_policy: dict[str, dict] = defaultdict(_empty_bucket)
    critical_divergences: list[dict] = []

    for finding, review, prediction, model in rows:
        review_ids.add(review.id)
        reviewed_study_ids.add(review.study_id)
        decisions[review.decision] += 1

        diverged = bool(finding.diverged_from_ai)
        if diverged:
            total_divergences += 1

        finding_bucket = by_finding[finding.finding_code]
        finding_bucket["reviewed_findings"] += 1
        finding_bucket["divergences"] += int(diverged)

        model_key = model.version if model else "unknown_model"
        model_bucket = by_model[model_key]
        model_bucket["reviewed_findings"] += 1
        model_bucket["divergences"] += int(diverged)

        policy_key = review.clinical_policy_version or "unknown_policy"
        policy_bucket = by_policy[policy_key]
        policy_bucket["reviewed_findings"] += 1
        policy_bucket["divergences"] += int(diverged)

        if diverged and finding.finding_code == "pneumothorax":
            critical_divergences.append({
                "study_id": review.study_id,
                "review_id": review.id,
                "finding_code": finding.finding_code,
                "decision": review.decision,
                "model_version": model_key,
                "clinical_policy_version": policy_key,
                "reviewed_at": review.reviewed_at,
            })

    for bucket_map in (by_finding, by_model, by_policy):
        for bucket in bucket_map.values():
            bucket["divergence_rate"] = _rate(bucket["divergences"], bucket["reviewed_findings"])

    return {
        "filters": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
            "model_version": model_version,
            "clinical_policy_version": clinical_policy_version,
        },
        "summary": {
            "reviewed_studies": len(reviewed_study_ids),
            "reviews": len(review_ids),
            "reviewed_findings": total_findings,
            "divergences": total_divergences,
            "divergence_rate": _rate(total_divergences, total_findings),
            "critical_divergences": len(critical_divergences),
        },
        "by_decision": dict(sorted(decisions.items())),
        "by_finding": dict(sorted(by_finding.items())),
        "by_model_version": dict(sorted(by_model.items())),
        "by_clinical_policy": dict(sorted(by_policy.items())),
        "critical_divergence_cases": critical_divergences[:50],
    }
