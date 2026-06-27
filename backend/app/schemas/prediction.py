from typing import List, Optional

from pydantic import BaseModel


class FindingOut(BaseModel):
    finding_code: str
    probability: float
    threshold: float
    is_positive: bool
    heatmap_url: Optional[str] = None


class PredictionResponse(BaseModel):
    study_id: str
    prediction_id: str
    model_version: str
    overall_status: str
    inference_time_ms: int
    findings: List[FindingOut]
    disclaimer: str
