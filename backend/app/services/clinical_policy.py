"""Versioned clinical policy for DOD Rx governance.

Model thresholds answer "is this finding positive?". Clinical policy answers
"what must the product do with that result?".
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants import CRITICAL_FINDINGS, FINDING_CODES
from app.models.clinical_policy import ClinicalPolicy

POLICY_VERSION = "dod-rx-cxr-policy-v0.1.0"

FINDING_LABELS = {
    "normal_no_critical_finding": "Sem achado critico",
    "pneumothorax": "Pneumotorax",
    "pleural_effusion": "Derrame pleural",
    "consolidation": "Consolidacao",
    "lung_opacity": "Opacidade pulmonar",
    "cardiomegaly": "Cardiomegalia",
}


def default_guardrails() -> dict:
    return {
        "must_have_human_review": True,
        "allow_autonomous_diagnosis": False,
        "max_autoclose_without_review_minutes": 0,
        "critical_findings_require_review": [
            "pneumothorax",
            "lung_opacity",
            "pleural_effusion",
            "consolidation",
            "cardiomegaly",
        ],
        "allowed_workflow_states_for_auto_actions": [],
        "triage_priority_rules": {
            "critical_first": True,
            "critical_codes": sorted(CRITICAL_FINDINGS),
            "sort_by": "criticality_then_inference_time_ms",
        },
        "finalization_rules": {
            "allow_auto_finalize": False,
            "minimum_review_fields": [
                "overall_impression",
                "per_finding_decision",
                "discrepancy_comment",
            ],
        },
        "disclaimer_rules": {
            "require_banner": True,
            "banner_text": (
                "Apoio a decisao em radiografia de torax. Nao e dispositivo "
                "diagnostico. Uso assistencial exige validacao clinica e regularizacao."
            ),
            "require_model_card_ack": True,
        },
        "audit_rules": {
            "log_policy_version_on_review": True,
            "log_policy_version_on_divergence": True,
        },
    }


def finding_rule(finding_code: str) -> dict:
    critical = finding_code in CRITICAL_FINDINGS
    return {
        "finding_code": finding_code,
        "label": FINDING_LABELS.get(finding_code, finding_code),
        "critical": critical,
        "worklist_priority": "critical" if critical else "routine",
        "requires_human_review": True,
        "action": "prioritize_worklist" if critical else "triage_review",
    }


def default_policy_payload() -> dict:
    findings = [finding_rule(code) for code in FINDING_CODES]
    guardrails = default_guardrails()
    return {
        **guardrails,
        "version": POLICY_VERSION,
        "name": "rx_triage_default",
        "scope": "chest_xray_mvp",
        "context": "clinical_rx_triage",
        "modality": ["CR", "DX"],
        "body_part": "CHEST",
        "clinical_output": "triage_and_suggested_findings",
        "human_review_required": True,
        "autonomous_diagnosis_allowed": False,
        "finalization_rule": "blocked_until_human_review",
        "critical_findings": sorted(CRITICAL_FINDINGS),
        "rules": {
            "guardrails": guardrails,
            "findings": findings,
        },
    }


def _rules_parts(rules: object) -> tuple[dict, list[dict]]:
    if isinstance(rules, dict):
        guardrails = {**default_guardrails(), **(rules.get("guardrails") or {})}
        findings = rules.get("findings") or []
        return guardrails, findings
    if isinstance(rules, list):
        return default_guardrails(), rules
    return default_guardrails(), []


def _structured_rules_from_payload(payload: dict) -> dict:
    guardrails, findings = _rules_parts(payload.get("rules"))
    guardrails = {
        **guardrails,
        "must_have_human_review": payload.get(
            "must_have_human_review",
            payload.get("human_review_required", guardrails["must_have_human_review"]),
        ),
        "allow_autonomous_diagnosis": payload.get(
            "allow_autonomous_diagnosis",
            payload.get("autonomous_diagnosis_allowed", guardrails["allow_autonomous_diagnosis"]),
        ),
        "max_autoclose_without_review_minutes": payload.get(
            "max_autoclose_without_review_minutes",
            guardrails["max_autoclose_without_review_minutes"],
        ),
        "critical_findings_require_review": payload.get(
            "critical_findings_require_review",
            guardrails["critical_findings_require_review"],
        ),
        "allowed_workflow_states_for_auto_actions": payload.get(
            "allowed_workflow_states_for_auto_actions",
            guardrails["allowed_workflow_states_for_auto_actions"],
        ),
        "triage_priority_rules": payload.get(
            "triage_priority_rules",
            guardrails["triage_priority_rules"],
        ) or guardrails["triage_priority_rules"],
        "finalization_rules": payload.get(
            "finalization_rules",
            guardrails["finalization_rules"],
        ) or guardrails["finalization_rules"],
        "disclaimer_rules": payload.get(
            "disclaimer_rules",
            guardrails["disclaimer_rules"],
        ) or guardrails["disclaimer_rules"],
        "audit_rules": payload.get(
            "audit_rules",
            guardrails["audit_rules"],
        ) or guardrails["audit_rules"],
    }
    return {"guardrails": guardrails, "findings": findings}


def serialize_policy(policy: ClinicalPolicy) -> dict:
    guardrails, findings = _rules_parts(policy.rules or [])
    return {
        "id": policy.id,
        "name": policy.name,
        "version": policy.version,
        "scope": policy.scope,
        "status": policy.status,
        "active": policy.active,
        "modality": ["CR", "DX"],
        "body_part": "CHEST",
        "clinical_output": "triage_and_suggested_findings",
        "human_review_required": policy.human_review_required,
        "autonomous_diagnosis_allowed": policy.autonomous_diagnosis_allowed,
        "finalization_rule": policy.finalization_rule,
        "critical_findings": sorted(
            rule["finding_code"] for rule in findings if rule.get("critical")
        ),
        "rule_guardrails": guardrails,
        "rules": findings,
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
        "activated_at": policy.activated_at,
        "created_by_user_id": policy.created_by_user_id,
        "notes": policy.notes,
    }


def seed_default_policy(db: Session) -> ClinicalPolicy:
    existing = db.query(ClinicalPolicy).filter_by(version=POLICY_VERSION).first()
    if existing:
        if not existing.active:
            db.query(ClinicalPolicy).filter(ClinicalPolicy.id != existing.id).update({
                ClinicalPolicy.active: False,
                ClinicalPolicy.status: "retired",
            })
            existing.active = True
            existing.status = "active"
            existing.activated_at = existing.activated_at or datetime.now(timezone.utc)
            db.flush()
        return existing

    payload = default_policy_payload()
    db.query(ClinicalPolicy).update({ClinicalPolicy.active: False, ClinicalPolicy.status: "retired"})
    policy = ClinicalPolicy(
        name=payload["name"],
        version=payload["version"],
        scope=payload["scope"],
        status="active",
        active=True,
        rules=payload["rules"],
        human_review_required=payload["human_review_required"],
        autonomous_diagnosis_allowed=payload["autonomous_diagnosis_allowed"],
        finalization_rule=payload["finalization_rule"],
        activated_at=datetime.now(timezone.utc),
        notes="Default MVP policy: human review required, no autonomous diagnosis.",
    )
    db.add(policy)
    db.flush()
    return policy


def active_policy(db: Session) -> dict:
    policy = db.query(ClinicalPolicy).filter_by(active=True).order_by(ClinicalPolicy.created_at.desc()).first()
    if not policy:
        policy = seed_default_policy(db)
        db.commit()
        db.refresh(policy)
    return serialize_policy(policy)


def list_policies(db: Session) -> list[dict]:
    policies = db.query(ClinicalPolicy).order_by(ClinicalPolicy.created_at.desc()).all()
    if not policies:
        policy = seed_default_policy(db)
        db.commit()
        db.refresh(policy)
        policies = [policy]
    return [serialize_policy(policy) for policy in policies]


def _validate_safe_policy_payload(payload: dict) -> None:
    """Keep clinical governance guardrails enforced at the write boundary."""
    structured_rules = _structured_rules_from_payload(payload)
    guardrails = structured_rules["guardrails"]
    finding_rules = structured_rules["findings"]

    if not guardrails.get("must_have_human_review", True):
        raise HTTPException(status_code=422,
                            detail="Clinical policy must have human review")
    if guardrails.get("allow_autonomous_diagnosis", False):
        raise HTTPException(status_code=422,
                            detail="Clinical policy cannot allow autonomous diagnosis")
    if guardrails.get("max_autoclose_without_review_minutes", 0) != 0:
        raise HTTPException(status_code=422,
                            detail="Clinical policy cannot autoclose without review")
    if guardrails.get("allowed_workflow_states_for_auto_actions", []):
        raise HTTPException(status_code=422,
                            detail="Clinical policy cannot enable automatic clinical actions")
    if guardrails.get("triage_priority_rules", {}).get("critical_first") is not True:
        raise HTTPException(status_code=422,
                            detail="Clinical policy must prioritize critical findings")
    if guardrails.get("finalization_rules", {}).get("allow_auto_finalize", False):
        raise HTTPException(status_code=422,
                            detail="Clinical policy cannot allow auto finalization")
    if guardrails.get("disclaimer_rules", {}).get("require_banner") is not True:
        raise HTTPException(status_code=422,
                            detail="Clinical policy must require governance banner")
    if guardrails.get("disclaimer_rules", {}).get("require_model_card_ack") is not True:
        raise HTTPException(status_code=422,
                            detail="Clinical policy must require model card acknowledgement")
    audit_rules = guardrails.get("audit_rules", {})
    if audit_rules.get("log_policy_version_on_review") is not True:
        raise HTTPException(status_code=422,
                            detail="Clinical policy must audit policy version on review")
    if audit_rules.get("log_policy_version_on_divergence") is not True:
        raise HTTPException(status_code=422,
                            detail="Clinical policy must audit policy version on divergence")

    if not payload.get("human_review_required", True):
        raise HTTPException(status_code=422,
                            detail="Human review must remain required")
    if payload.get("autonomous_diagnosis_allowed", False):
        raise HTTPException(status_code=422,
                            detail="Autonomous diagnosis is not allowed")
    if payload.get("finalization_rule") != "blocked_until_human_review":
        raise HTTPException(status_code=422,
                            detail="Finalization must stay blocked until human review")

    for rule in finding_rules:
        if not rule.get("finding_code"):
            raise HTTPException(status_code=422,
                                detail="Every clinical rule needs a finding_code")
        if rule.get("requires_human_review") is False:
            raise HTTPException(status_code=422,
                                detail="Clinical rules cannot disable human review")


def create_policy(db: Session, payload: dict, created_by_user_id: str | None = None) -> ClinicalPolicy:
    _validate_safe_policy_payload(payload)
    existing = db.query(ClinicalPolicy).filter_by(version=payload["version"]).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Clinical policy version already exists")

    if payload.get("activate"):
        db.query(ClinicalPolicy).update({ClinicalPolicy.active: False, ClinicalPolicy.status: "retired"})

    policy = ClinicalPolicy(
        name=payload.get("name") or "rx_triage_default",
        version=payload["version"],
        scope=payload["scope"],
        status="active" if payload.get("activate") else "draft",
        active=bool(payload.get("activate")),
        rules=_structured_rules_from_payload(payload),
        human_review_required=payload.get("human_review_required", True),
        autonomous_diagnosis_allowed=payload.get("autonomous_diagnosis_allowed", False),
        finalization_rule=payload["finalization_rule"],
        activated_at=datetime.now(timezone.utc) if payload.get("activate") else None,
        created_by_user_id=created_by_user_id,
        notes=payload.get("notes"),
    )
    db.add(policy)
    db.flush()
    return policy


def activate_policy(db: Session, policy_id: str) -> ClinicalPolicy:
    policy = db.query(ClinicalPolicy).filter_by(id=policy_id).first()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Clinical policy not found")
    _validate_safe_policy_payload({
        "rules": policy.rules or [],
        "human_review_required": policy.human_review_required,
        "autonomous_diagnosis_allowed": policy.autonomous_diagnosis_allowed,
        "finalization_rule": policy.finalization_rule,
    })
    db.query(ClinicalPolicy).filter(ClinicalPolicy.id != policy.id).update({
        ClinicalPolicy.active: False,
        ClinicalPolicy.status: "retired",
    })
    policy.active = True
    policy.status = "active"
    policy.activated_at = datetime.now(timezone.utc)
    db.flush()
    return policy


def priority_for_overall(overall_status: str | None) -> str:
    return "critical" if overall_status == "abnormal_critical" else "routine"
