from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base, GUID, new_uuid


class Prediction(Base):
    """A single AI inference run over a study. Re-running with a new model
    creates a NEW Prediction row — old predictions are never overwritten."""

    __tablename__ = "predictions"

    id = Column(GUID, primary_key=True, default=new_uuid)
    study_id = Column(GUID, ForeignKey("studies.id"), nullable=False, index=True)
    model_version_id = Column(GUID, ForeignKey("model_versions.id"), nullable=False)
    overall_status = Column(String, nullable=False)
    inference_time_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    study = relationship("Study", back_populates="predictions")
    model_version = relationship("ModelVersion")
    findings = relationship(
        "PredictionFinding", back_populates="prediction", cascade="all, delete-orphan"
    )


class PredictionFinding(Base):
    __tablename__ = "prediction_findings"

    id = Column(GUID, primary_key=True, default=new_uuid)
    prediction_id = Column(GUID, ForeignKey("predictions.id"), nullable=False, index=True)
    finding_code = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    is_positive = Column(Boolean, default=False)
    heatmap_path = Column(String, nullable=True)

    prediction = relationship("Prediction", back_populates="findings")
