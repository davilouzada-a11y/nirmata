from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base, GUID, new_uuid


class Study(Base):
    """One imaging study. For the MVP a study holds a single chest X-ray image
    (DICOM/PNG/JPG); the `images` table from the blueprint is collapsed into the
    study's image fields to keep the first iteration lean."""

    __tablename__ = "studies"

    id = Column(GUID, primary_key=True, default=new_uuid)
    patient_id = Column(GUID, ForeignKey("patients.id"), nullable=True)
    patient_code = Column(String, nullable=False)  # denormalized for quick listing
    modality = Column(String, default="CR")
    body_part = Column(String, default="CHEST")
    view = Column(String, default="PA")  # PA / AP / LAT
    status = Column(String, default="uploaded", index=True)

    # Image storage
    image_path = Column(String, nullable=False)
    image_format = Column(String, default="png")  # dicom / png / jpg
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient")
    predictions = relationship("Prediction", back_populates="study", order_by="Prediction.created_at")
    reviews = relationship("Review", back_populates="study", order_by="Review.reviewed_at")
