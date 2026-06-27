from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.constants import REVIEW_DECISIONS


class ReviewFindingIn(BaseModel):
    finding_code: str
    final_label: bool
    comment: Optional[str] = None


class ReviewCreate(BaseModel):
    decision: str  # confirmed | corrected | rejected
    final_findings: List[ReviewFindingIn]
    final_report: str
    # The prediction the reviewer is acting on (optional; defaults to latest).
    prediction_id: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def _valid_decision(cls, v: str) -> str:
        if v not in REVIEW_DECISIONS:
            raise ValueError(f"decision must be one of {sorted(REVIEW_DECISIONS)}")
        return v


class ReviewFindingOut(BaseModel):
    finding_code: str
    final_label: bool
    diverged_from_ai: bool
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewOut(BaseModel):
    id: str
    study_id: str
    prediction_id: Optional[str]
    reviewer_id: str
    decision: str
    final_report: str
    reviewed_at: datetime
    findings: List[ReviewFindingOut]

    model_config = ConfigDict(from_attributes=True)
