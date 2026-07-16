from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class StudyOut(BaseModel):
    id: str
    patient_code: str
    modality: str
    body_part: str
    view: str
    status: str
    image_format: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyListItem(BaseModel):
    """Row for the pending-studies queue, enriched with read priority."""

    id: str
    patient_code: str
    view: str
    status: str
    created_at: datetime
    overall_status: Optional[str] = None
    priority: str = "routine"  # "critical" | "routine"

    model_config = ConfigDict(from_attributes=True)


class StudyStateChangeRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        reason = value.strip()
        if not reason:
            raise ValueError("reason is required")
        return reason
