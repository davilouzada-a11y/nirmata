from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey

from app.core.db import Base, GUID, new_uuid


class AuditLog(Base):
    """Append-only audit trail. Every clinically meaningful action is logged
    with the acting user, the affected entity and a JSON payload."""

    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=new_uuid)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # e.g. study.upload, study.predict, study.review
    entity = Column(String, nullable=False)  # e.g. study
    entity_id = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
