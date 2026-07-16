from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ClinicalPolicyCreate(BaseModel):
    name: str = "rx_triage_default"
    version: str
    scope: str
    rules: list[dict[str, Any]] | dict[str, Any]
    human_review_required: bool = True
    autonomous_diagnosis_allowed: bool = False
    finalization_rule: str = "blocked_until_human_review"
    must_have_human_review: bool = True
    allow_autonomous_diagnosis: bool = False
    max_autoclose_without_review_minutes: int = 0
    critical_findings_require_review: list[str] = []
    allowed_workflow_states_for_auto_actions: list[str] = []
    triage_priority_rules: dict[str, Any] = {}
    finalization_rules: dict[str, Any] = {}
    disclaimer_rules: dict[str, Any] = {}
    audit_rules: dict[str, Any] = {}
    notes: Optional[str] = None
    activate: bool = False

    @field_validator("name", "version", "scope", "finalization_rule")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("rules")
    @classmethod
    def _has_rules(cls, value: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any]:
        if not value:
            raise ValueError("at least one clinical rule is required")
        if isinstance(value, dict) and not value.get("findings"):
            raise ValueError("structured clinical rules require findings")
        return value


class ClinicalPolicyOut(BaseModel):
    id: str
    name: str
    version: str
    scope: str
    status: str
    active: bool
    modality: list[str]
    body_part: str
    clinical_output: str
    human_review_required: bool
    autonomous_diagnosis_allowed: bool
    finalization_rule: str
    critical_findings: list[str]
    rule_guardrails: dict[str, Any]
    rules: list[dict[str, Any]]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    created_by_user_id: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
