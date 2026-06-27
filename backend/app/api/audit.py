from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("/studies/{study_id}")
def study_audit_trail(study_id: str, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    """Full chronological audit trail for one study."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity == "study", AuditLog.entity_id == study_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [
        {"action": l.action, "user_id": l.user_id, "payload": l.payload,
         "created_at": l.created_at}
        for l in logs
    ]
