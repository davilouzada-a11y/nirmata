from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String

from app.core.db import Base, GUID, new_uuid


class ClinicalPolicy(Base):
    """Versioned clinical rules independent from model thresholds."""

    __tablename__ = "clinical_policies"

    id = Column(GUID, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False, default="rx_triage_default")
    version = Column(String, nullable=False, unique=True)
    scope = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft", index=True)
    active = Column(Boolean, default=False, index=True)
    rules = Column(JSON, nullable=False, default=list)
    human_review_required = Column(Boolean, default=True, nullable=False)
    autonomous_diagnosis_allowed = Column(Boolean, default=False, nullable=False)
    finalization_rule = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    activated_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
