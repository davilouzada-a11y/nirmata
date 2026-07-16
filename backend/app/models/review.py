from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base, GUID, new_uuid


class Review(Base):
    """A mandatory human review that finalizes a study. Always references the
    prediction (and thus the model version) it was made against."""

    __tablename__ = "reviews"

    id = Column(GUID, primary_key=True, default=new_uuid)
    study_id = Column(GUID, ForeignKey("studies.id"), nullable=False, index=True)
    prediction_id = Column(GUID, ForeignKey("predictions.id"), nullable=True)
    reviewer_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False)  # confirmed | corrected | rejected
    clinical_policy_version = Column(String, nullable=True)
    final_report = Column(Text, nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    study = relationship("Study", back_populates="reviews")
    findings = relationship(
        "ReviewFinding", back_populates="review", cascade="all, delete-orphan"
    )


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id = Column(GUID, primary_key=True, default=new_uuid)
    review_id = Column(GUID, ForeignKey("reviews.id"), nullable=False, index=True)
    finding_code = Column(String, nullable=False)
    final_label = Column(Boolean, nullable=False)
    # True when the human label differs from the AI's is_positive — persisted so
    # AI-vs-human divergence is always queryable.
    diverged_from_ai = Column(Boolean, default=False)
    comment = Column(Text, nullable=True)

    review = relationship("Review", back_populates="findings")
