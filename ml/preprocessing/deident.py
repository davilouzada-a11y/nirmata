"""DICOM de-identification (automatic PHI removal).

Implements a pragmatic subset of the DICOM Basic Application Level
Confidentiality Profile (PS3.15 Annex E): identifying attributes are removed,
emptied or pseudonymized; UIDs are consistently remapped so study/series/instance
relationships survive while linkage to the original identity is broken; private
tags, overlays and curves (which can carry burned-in PHI) are stripped.

The function returns the cleaned dataset plus a structured report of every action
taken, so the pipeline (and the backend audit log) can prove what was removed.

Clinically useful, low-risk attributes (PatientSex, PatientAge, view/modality,
pixel-calibration tags) are kept by default because the downstream model needs
them; this is configurable via the policy.

NOTE: this addresses *metadata* PHI. Burned-in pixel text is flagged for review
(see `pipeline.process_dicom`) but not OCR-redacted here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

DEIDENT_METHOD = "nirmata-basic-confidentiality v1"

# action ∈ {remove, empty, pseudonymize, regenerate_uid}
# Keyword-based policy keeps it readable; tags are resolved via pydicom.
DEFAULT_POLICY: dict[str, str] = {
    # Direct identifiers
    "PatientName": "pseudonymize",
    "PatientID": "pseudonymize",
    "OtherPatientIDs": "remove",
    "OtherPatientIDsSequence": "remove",
    "PatientBirthDate": "empty",
    "PatientBirthTime": "empty",
    "PatientAddress": "remove",
    "PatientTelephoneNumbers": "remove",
    "PatientMotherBirthName": "remove",
    "MilitaryRank": "remove",
    "EthnicGroup": "remove",
    "PatientComments": "remove",
    # Care-site / people
    "InstitutionName": "remove",
    "InstitutionAddress": "remove",
    "InstitutionalDepartmentName": "remove",
    "ReferringPhysicianName": "empty",
    "ReferringPhysicianTelephoneNumbers": "remove",
    "PerformingPhysicianName": "remove",
    "NameOfPhysiciansReadingStudy": "remove",
    "OperatorsName": "remove",
    "RequestingPhysician": "remove",
    "StationName": "remove",
    "DeviceSerialNumber": "remove",
    # Identifying numbers / accession
    "AccessionNumber": "empty",
    "StudyID": "empty",
    # Dates & times that can re-identify
    "StudyDate": "empty",
    "SeriesDate": "empty",
    "AcquisitionDate": "empty",
    "ContentDate": "empty",
    "InstanceCreationDate": "empty",
    "StudyTime": "empty",
    "SeriesTime": "empty",
    "AcquisitionTime": "empty",
    "ContentTime": "empty",
    # UIDs — regenerate consistently (preserve relationships, break linkage)
    "StudyInstanceUID": "regenerate_uid",
    "SeriesInstanceUID": "regenerate_uid",
    "SOPInstanceUID": "regenerate_uid",
    "FrameOfReferenceUID": "regenerate_uid",
    "MediaStorageSOPInstanceUID": "regenerate_uid",
}

# Attributes deliberately KEPT (documented so the policy is auditable).
RETAINED_FOR_MODELLING = ("PatientSex", "PatientAge", "Modality", "ViewPosition",
                          "BodyPartExamined", "PhotometricInterpretation",
                          "RescaleSlope", "RescaleIntercept", "WindowCenter", "WindowWidth")


@dataclass
class DeidentReport:
    pseudo_patient_id: str
    actions: list[dict] = field(default_factory=list)
    private_tags_removed: int = 0
    overlay_groups_removed: int = 0
    retained: list[str] = field(default_factory=list)

    def add(self, keyword: str, action: str):
        self.actions.append({"attribute": keyword, "action": action})

    def summary(self) -> dict:
        return {
            "pseudo_patient_id": self.pseudo_patient_id,
            "removed_or_modified": len(self.actions),
            "private_tags_removed": self.private_tags_removed,
            "overlay_groups_removed": self.overlay_groups_removed,
            "retained": self.retained,
            "method": DEIDENT_METHOD,
        }


def pseudonymize_id(value: str, salt: str) -> str:
    """Deterministic, non-reversible short pseudonym for a patient identifier."""
    digest = hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()
    return f"ANON-{digest[:12].upper()}"


def _regen_uid(original: str, salt: str) -> str:
    """Deterministically map a UID to a new one under the 2.25 root."""
    digest = hashlib.sha256(f"{salt}:uid:{original}".encode()).hexdigest()
    numeric = str(int(digest, 16))
    return ("2.25." + numeric)[:64]


def deidentify_dataset(ds, salt: str = "nirmata", policy: dict[str, str] | None = None):
    """Return (cleaned_dataset, DeidentReport). Mutates a copy-safe view of `ds`."""
    policy = policy or DEFAULT_POLICY
    original_pid = str(getattr(ds, "PatientID", "") or "unknown")
    pseudo = pseudonymize_id(original_pid, salt)
    report = DeidentReport(pseudo_patient_id=pseudo)

    # 1) Apply the keyword policy.
    for keyword, action in policy.items():
        if keyword not in ds:
            continue
        if action == "remove":
            delattr(ds, keyword)
            report.add(keyword, "removed")
        elif action == "empty":
            setattr(ds, keyword, "")
            report.add(keyword, "emptied")
        elif action == "pseudonymize":
            setattr(ds, keyword, pseudo if keyword == "PatientID" else pseudo)
            report.add(keyword, "pseudonymized")
        elif action == "regenerate_uid":
            setattr(ds, keyword, _regen_uid(str(getattr(ds, keyword)), salt))
            report.add(keyword, "uid_regenerated")

    # Keep file-meta SOP Instance UID consistent with the dataset's.
    if hasattr(ds, "file_meta") and "SOPInstanceUID" in ds:
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID

    # 2) Strip private tags (vendor blobs may embed PHI).
    before = len(list(ds))
    ds.remove_private_tags()
    report.private_tags_removed = before - len(list(ds))

    # 3) Remove overlay (0x60xx) and curve (0x50xx) groups — possible burned-in PHI.
    to_delete = [elem.tag for elem in ds
                 if 0x5000 <= elem.tag.group <= 0x50FF or 0x6000 <= elem.tag.group <= 0x60FF]
    for tag in to_delete:
        del ds[tag]
    report.overlay_groups_removed = len(to_delete)

    # 4) Stamp the de-identification provenance (PS3.15 required attributes).
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = DEIDENT_METHOD

    report.retained = [k for k in RETAINED_FOR_MODELLING if k in ds]
    return ds, report
