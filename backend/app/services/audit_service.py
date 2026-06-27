"""Centralized audit logging."""
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log(db: Session, *, user_id: str | None, action: str, entity: str,
        entity_id: str | None = None, payload: dict | None = None) -> AuditLog:
    entry = AuditLog(
        user_id=user_id, action=action, entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None, payload=payload,
    )
    db.add(entry)
    db.flush()
    return entry
