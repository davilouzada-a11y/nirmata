"""End-to-end test of the clinical workflow against a temp SQLite DB.

Covers: login → upload → predict → (finalize blocked before review) →
review → finalized, plus audit trail and AI/human divergence persistence.
"""
import io
import os
import tempfile

import pytest

# Configure an isolated DB + storage BEFORE importing the app.
_tmp = tempfile.mkdtemp(prefix="radiografia-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'test.db')}"
os.environ["STORAGE_DIR"] = os.path.join(_tmp, "storage")
os.environ["ML_BACKEND"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.core.db import SessionLocal, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.audit import AuditLog  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.clinical_policy import default_policy_payload  # noqa: E402
from app.services.study_service import get_or_create_model_version  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    try:
        get_or_create_model_version(db)
        if not db.query(User).filter_by(email="doc@example.com").first():
            db.add(User(name="Dr Test", email="doc@example.com", role="radiologist",
                        hashed_password=hash_password("secret123"), active=True))
        if not db.query(User).filter_by(email="tech@example.com").first():
            db.add(User(name="Tech", email="tech@example.com", role="technician",
                        hashed_password=hash_password("secret123"), active=True))
        if not db.query(User).filter_by(email="admin@example.com").first():
            db.add(User(name="Admin", email="admin@example.com", role="admin",
                        hashed_password=hash_password("secret123"), active=True))
        db.commit()
    finally:
        db.close()
    yield


def _token(email="doc@example.com", password="secret123"):
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(email="doc@example.com"):
    return {"Authorization": f"Bearer {_token(email)}"}


def _policy_payload(version="dod-rx-cxr-policy-test-v0.2.0", activate=False):
    payload = default_policy_payload()
    return {
        "version": version,
        "scope": payload["scope"],
        "rules": payload["rules"],
        "human_review_required": True,
        "autonomous_diagnosis_allowed": False,
        "finalization_rule": "blocked_until_human_review",
        "activate": activate,
    }


def _upload(headers):
    img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes-for-testing" * 20)
    r = client.post(
        "/studies/upload",
        data={"patient_code": "P-001", "view": "PA"},
        files={"file": ("cxr.png", img, "image/png")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_login_required():
    assert client.get("/studies").status_code == 401


def test_full_workflow():
    headers = _auth()
    study_id = _upload(headers)

    # Study starts in `uploaded`.
    assert client.get(f"/studies/{study_id}", headers=headers).json()["status"] == "uploaded"

    # Cannot review before a prediction exists.
    early = client.post(f"/studies/{study_id}/review",
                        json={"decision": "confirmed", "final_findings": [], "final_report": "x"},
                        headers=headers)
    assert early.status_code == 409

    # Run inference.
    pred = client.post(f"/studies/{study_id}/predict", headers=headers)
    assert pred.status_code == 200, pred.text
    body = pred.json()
    assert body["disclaimer"]
    assert len(body["findings"]) == 6
    assert client.get(f"/studies/{study_id}", headers=headers).json()["status"] == "predicted"

    # Image and (any) heatmap are retrievable.
    assert client.get(f"/studies/{study_id}/image", headers=headers).status_code == 200

    # Review with a deliberate divergence from the AI on one finding.
    ai = {f["finding_code"]: f["is_positive"] for f in body["findings"]}
    flip_code = "consolidation"
    final_findings = [
        {"finding_code": c, "final_label": (not v if c == flip_code else v),
         "comment": "divergência" if c == flip_code else None}
        for c, v in ai.items()
    ]
    review = client.post(f"/studies/{study_id}/review",
                         json={"decision": "corrected", "final_findings": final_findings,
                               "final_report": "Laudo final de teste."},
                         headers=headers)
    assert review.status_code == 201, review.text
    assert review.json()["clinical_policy_version"] == "dod-rx-cxr-policy-v0.1.0"
    diverged = [f for f in review.json()["findings"] if f["diverged_from_ai"]]
    assert any(f["finding_code"] == flip_code for f in diverged)

    # Study is finalized.
    assert client.get(f"/studies/{study_id}", headers=headers).json()["status"] == "finalized"

    # Audit trail records upload, predict and review.
    trail = client.get(f"/audit/studies/{study_id}", headers=headers).json()
    actions = {e["action"] for e in trail}
    assert {
        "study.upload",
        "policy.denied",
        "study.predict",
        "image.viewed",
        "policy.evaluated",
        "study.review",
    } <= actions
    denied_events = [e for e in trail if e["action"] == "policy.denied"]
    assert denied_events[-1]["payload"]["reason"] == "invalid_review_state"
    evaluated_events = [e for e in trail if e["action"] == "policy.evaluated"]
    assert evaluated_events[-1]["payload"]["allowed"] is True
    assert evaluated_events[-1]["payload"]["clinical_policy_version"] == "dod-rx-cxr-policy-v0.1.0"
    review_events = [e for e in trail if e["action"] == "study.review"]
    assert review_events[-1]["payload"]["clinical_policy_version"] == "dod-rx-cxr-policy-v0.1.0"


def test_technician_cannot_review():
    tech = _auth("tech@example.com")
    study_id = _upload(tech)
    client.post(f"/studies/{study_id}/predict", headers=tech)
    r = client.post(f"/studies/{study_id}/review",
                    json={"decision": "confirmed", "final_findings": [], "final_report": "x"},
                    headers=tech)
    assert r.status_code == 403


def test_admin_can_create_and_activate_clinical_policy():
    headers = _auth("admin@example.com")
    created = client.post("/models/policies",
                          json=_policy_payload("dod-rx-cxr-policy-test-v0.2.0"),
                          headers=headers)
    assert created.status_code == 201, created.text
    policy = created.json()
    assert policy["name"] == "rx_triage_default"
    assert policy["version"] == "dod-rx-cxr-policy-test-v0.2.0"
    assert policy["active"] is False
    assert policy["status"] == "draft"
    assert policy["human_review_required"] is True
    assert policy["created_by_user_id"]

    activated = client.post(f"/models/policies/{policy['id']}/activate", headers=headers)
    assert activated.status_code == 200, activated.text
    assert activated.json()["active"] is True
    assert activated.json()["status"] == "active"
    assert activated.json()["activated_at"]

    active = client.get("/models/policy/active", headers=headers).json()
    assert active["version"] == "dod-rx-cxr-policy-test-v0.2.0"

    db = SessionLocal()
    try:
        actions = {
            row.action
            for row in db.query(AuditLog).filter(AuditLog.entity == "clinical_policy").all()
        }
        assert {"policy.create", "policy.activate"} <= actions
    finally:
        db.close()


def test_non_admin_cannot_manage_clinical_policy():
    headers = _auth("tech@example.com")
    r = client.post("/models/policies",
                    json=_policy_payload("dod-rx-cxr-policy-test-forbidden"),
                    headers=headers)
    assert r.status_code == 403


def test_policy_cannot_disable_human_review_or_allow_autonomous_diagnosis():
    headers = _auth("admin@example.com")
    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe")
    unsafe["human_review_required"] = False
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-2")
    unsafe["autonomous_diagnosis_allowed"] = True
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-3")
    unsafe["must_have_human_review"] = False
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-4")
    unsafe["allow_autonomous_diagnosis"] = True
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-5")
    unsafe["max_autoclose_without_review_minutes"] = 5
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-6")
    unsafe["allowed_workflow_states_for_auto_actions"] = ["predicted"]
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-7")
    unsafe["finalization_rules"] = {"allow_auto_finalize": True}
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-8")
    unsafe["disclaimer_rules"] = {"require_banner": False, "require_model_card_ack": True}
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422

    unsafe = _policy_payload("dod-rx-cxr-policy-unsafe-9")
    unsafe["audit_rules"] = {
        "log_policy_version_on_review": False,
        "log_policy_version_on_divergence": True,
    }
    assert client.post("/models/policies", json=unsafe, headers=headers).status_code == 422


def test_reprediction_creates_new_prediction():
    headers = _auth()
    study_id = _upload(headers)
    p1 = client.post(f"/studies/{study_id}/predict", headers=headers).json()["prediction_id"]
    p2 = client.post(f"/studies/{study_id}/predict", headers=headers).json()["prediction_id"]
    assert p1 != p2  # old prediction preserved, new one created


def test_hold_and_reopen_require_reason_and_audit_state_change():
    headers = _auth()
    study_id = _upload(headers)
    prediction_id = client.post(f"/studies/{study_id}/predict", headers=headers).json()["prediction_id"]

    blank = client.post(f"/studies/{study_id}/hold", json={"reason": "   "}, headers=headers)
    assert blank.status_code == 422

    held = client.post(
        f"/studies/{study_id}/hold",
        json={"reason": "Aguardar revisao senior por achado critico."},
        headers=headers,
    )
    assert held.status_code == 200, held.text
    assert held.json()["status"] == "blocked"

    review = client.post(
        f"/studies/{study_id}/review",
        json={
            "prediction_id": prediction_id,
            "decision": "confirmed",
            "final_findings": [],
            "final_report": "Laudo final de teste.",
        },
        headers=headers,
    )
    assert review.status_code == 409

    reopened = client.post(
        f"/studies/{study_id}/reopen",
        json={"reason": "Revisao senior liberou continuidade."},
        headers=headers,
    )
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["status"] == "predicted"

    trail = client.get(f"/audit/studies/{study_id}", headers=headers).json()
    actions = [e["action"] for e in trail]
    assert "study.hold" in actions
    assert "study.reopened" in actions
    assert "policy.denied" in actions
    hold = [e for e in trail if e["action"] == "study.hold"][-1]
    assert hold["payload"]["previous_status"] == "predicted"
    assert hold["payload"]["new_status"] == "blocked"
    reopen = [e for e in trail if e["action"] == "study.reopened"][-1]
    assert reopen["payload"]["previous_status"] == "blocked"
    assert reopen["payload"]["new_status"] == "predicted"
    assert reopen["payload"]["prediction_id"] == prediction_id


def test_stats_endpoint():
    headers = _auth()
    stats = client.get("/studies/stats", headers=headers).json()
    assert stats["total_studies"] >= 1
    assert "by_status" in stats and "by_overall_status" in stats
    assert 0.0 <= stats["divergence_rate"] <= 1.0
    # The corrected review from test_full_workflow should register a divergence.
    assert stats["reviews_with_divergence"] >= 1


def test_governance_divergence_report():
    headers = _auth()
    report = client.get("/governance/divergence", headers=headers)
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["summary"]["reviews"] >= 1
    assert body["summary"]["reviewed_findings"] >= 6
    assert body["summary"]["divergences"] >= 1
    assert body["summary"]["divergence_rate"] > 0
    assert body["by_decision"]["corrected"] >= 1
    assert body["by_finding"]["consolidation"]["divergences"] >= 1
    assert "dod-rx-cxr-policy-v0.1.0" in body["by_clinical_policy"]

    by_model = client.get(
        "/governance/divergence?model_version=cxr-densenet-v0.1.0",
        headers=headers,
    ).json()
    assert by_model["filters"]["model_version"] == "cxr-densenet-v0.1.0"
    assert by_model["summary"]["reviewed_findings"] >= 6

    by_policy = client.get(
        "/governance/divergence?clinical_policy_version=dod-rx-cxr-policy-v0.1.0",
        headers=headers,
    ).json()
    assert by_policy["filters"]["clinical_policy_version"] == "dod-rx-cxr-policy-v0.1.0"
    assert list(by_policy["by_clinical_policy"]) == ["dod-rx-cxr-policy-v0.1.0"]


def test_dicom_upload_is_deidentified_on_disk():
    """A DICOM with PHI must be stripped before it is persisted, and the
    de-identification must be recorded in the audit trail."""
    import pydicom
    from ml.preprocessing.synthetic import synthetic_dicom

    headers = _auth()
    dicom_bytes = synthetic_dicom(seed=42)
    # Sanity: the source really does carry PHI.
    assert str(pydicom.dcmread(io.BytesIO(dicom_bytes), force=True).PatientName) == "Doe^John"

    r = client.post(
        "/studies/upload",
        data={"patient_code": "ANON-CASE", "view": "PA"},
        files={"file": ("scan.dcm", io.BytesIO(dicom_bytes), "application/dicom")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    study = r.json()
    assert study["image_format"] == "dicom"

    # Read the file the server actually stored and confirm PHI is gone.
    detail = client.get(f"/studies/{study['id']}", headers=headers).json()  # noqa: F841
    img = client.get(f"/studies/{study['id']}/image", headers=headers)
    assert img.status_code == 200
    stored = pydicom.dcmread(io.BytesIO(img.content), force=True)
    assert stored.PatientIdentityRemoved == "YES"
    assert str(stored.PatientName).startswith("ANON-")
    assert "InstitutionName" not in stored
    assert "DeviceSerialNumber" not in stored

    # Audit trail records the de-identification with a summary.
    trail = client.get(f"/audit/studies/{study['id']}", headers=headers).json()
    deid = [e for e in trail if e["action"] == "study.deidentify"]
    assert deid and deid[0]["payload"]["removed_or_modified"] >= 1


def test_corrupt_dicom_is_rejected_not_stored():
    headers = _auth()
    bad = io.BytesIO(b"DICM-not-really" + b"\x00" * 50)
    r = client.post(
        "/studies/upload",
        data={"patient_code": "X", "view": "PA"},
        files={"file": ("broken.dcm", bad, "application/dicom")},
        headers=headers,
    )
    assert r.status_code == 422


def test_demo_seeder_populates_mixed_states():
    from app import demo

    demo.run()
    headers = _auth()
    studies = client.get("/studies", headers=headers).json()
    codes = {s["patient_code"] for s in studies}
    assert {"P-1001", "P-1002", "P-1003"} <= codes
    statuses = {s["status"] for s in studies}
    # Demo creates studies in several workflow states.
    assert "uploaded" in statuses and "finalized" in statuses
