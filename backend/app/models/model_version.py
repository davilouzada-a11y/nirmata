from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, JSON

from app.core.db import Base, GUID, new_uuid


class ModelVersion(Base):
    """A trained model release. Predictions reference the exact version used so
    AI output is always traceable and reproducible for audit."""

    __tablename__ = "model_versions"

    id = Column(GUID, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, unique=True)
    training_dataset = Column(String, nullable=True)
    threshold_config = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
