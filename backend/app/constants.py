"""Clinical constants shared across the backend.

The MVP scope is chest X-ray (CR/DX) multi-label triage with a fixed set of
findings, exactly as defined in the project blueprint.
"""

# Finding codes for the MVP (order matters for stable JSON output).
FINDING_CODES = [
    "normal_no_critical_finding",
    "pneumothorax",
    "pleural_effusion",
    "consolidation",
    "cardiomegaly",
]

# Findings that, when positive, make a study clinically critical (priority read).
CRITICAL_FINDINGS = {"pneumothorax"}

# Default per-class decision thresholds (calibrated offline in ml/training).
DEFAULT_THRESHOLDS = {
    "normal_no_critical_finding": 0.50,
    "pneumothorax": 0.45,
    "pleural_effusion": 0.62,
    "consolidation": 0.55,
    "cardiomegaly": 0.60,
}

# Thresholds for the TorchXRayVision pretrained model (ML_BACKEND=xrv). Its
# sigmoid outputs aren't locally calibrated, so we use conservative operating
# points with a lower bar for the critical finding (higher sensitivity).
XRV_DEFAULT_THRESHOLDS = {
    "normal_no_critical_finding": 0.50,
    "pneumothorax": 0.40,
    "pleural_effusion": 0.50,
    "consolidation": 0.50,
    "cardiomegaly": 0.50,
}

# Study lifecycle states. Transitions are enforced in study_service.
STUDY_STATES = [
    "uploaded",
    "processing",
    "predicted",
    "under_review",
    "reviewed",
    "finalized",
]

# Overall status buckets returned by inference.
OVERALL_NORMAL = "normal"
OVERALL_ABNORMAL_NONCRITICAL = "abnormal_noncritical"
OVERALL_ABNORMAL_CRITICAL = "abnormal_critical"

# Review decisions.
REVIEW_DECISIONS = {"confirmed", "corrected", "rejected"}

DISCLAIMER = "Resultado automatizado sujeito à revisão médica obrigatória."
