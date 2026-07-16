from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_governance_admin
from app.core.db import get_db
from app.models.model_version import ModelVersion
from app.models.user import User
from app.schemas.clinical_policy import ClinicalPolicyCreate, ClinicalPolicyOut
from app.services import audit_service
from app.services.clinical_policy import (
    activate_policy,
    active_policy,
    create_policy,
    list_policies,
    serialize_policy,
)

router = APIRouter()


@router.get("/versions")
def list_model_versions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    versions = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    return [
        {"id": m.id, "name": m.name, "version": m.version,
         "training_dataset": m.training_dataset, "threshold_config": m.threshold_config,
         "created_at": m.created_at}
        for m in versions
    ]


@router.get("/policy/active")
def get_active_policy(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ClinicalPolicyOut:
    return active_policy(db)


@router.get("/policies")
def get_policy_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ClinicalPolicyOut]:
    return list_policies(db)


@router.post("/policies", status_code=status.HTTP_201_CREATED)
def create_clinical_policy(
    payload: ClinicalPolicyCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_governance_admin),
) -> ClinicalPolicyOut:
    policy = create_policy(db, payload.model_dump(), created_by_user_id=user.id)
    audit_service.log(
        db,
        user_id=user.id,
        action="policy.create",
        entity="clinical_policy",
        entity_id=policy.id,
        payload={
            "version": policy.version,
            "name": policy.name,
            "scope": policy.scope,
            "status": policy.status,
            "active": policy.active,
            "human_review_required": policy.human_review_required,
            "autonomous_diagnosis_allowed": policy.autonomous_diagnosis_allowed,
        },
    )
    db.commit()
    db.refresh(policy)
    return serialize_policy(policy)


@router.post("/policies/{policy_id}/activate")
def activate_clinical_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_governance_admin),
) -> ClinicalPolicyOut:
    previous = active_policy(db)
    policy = activate_policy(db, policy_id)
    audit_service.log(
        db,
        user_id=user.id,
        action="policy.activate",
        entity="clinical_policy",
        entity_id=policy.id,
        payload={
            "previous_version": previous["version"],
            "new_version": policy.version,
            "new_status": policy.status,
            "scope": policy.scope,
        },
    )
    db.commit()
    db.refresh(policy)
    return serialize_policy(policy)
