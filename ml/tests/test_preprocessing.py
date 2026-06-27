"""Verify de-identification actually removes PHI and the pipeline produces a
display image. Uses synthetic DICOMs only (no real patient data)."""
import io

import pydicom

from ml.preprocessing.synthetic import synthetic_dicom
from ml.preprocessing.deident import deidentify_dataset, pseudonymize_id
from ml.preprocessing.pipeline import process_dicom

PHI_TAGS = [
    "PatientName", "PatientBirthDate", "PatientAddress", "InstitutionName",
    "ReferringPhysicianName", "OperatorsName", "DeviceSerialNumber",
]


def _read(b):
    return pydicom.dcmread(io.BytesIO(b), force=True)


def test_phi_is_removed_or_emptied():
    ds = _read(synthetic_dicom(seed=1))
    assert ds.PatientName == "Doe^John"  # PHI present before

    clean, report = deidentify_dataset(ds, salt="test-salt")

    # Direct identifiers gone or pseudonymized.
    assert "PatientName" in clean and str(clean.PatientName).startswith("ANON-")
    assert str(clean.PatientID).startswith("ANON-")
    for tag in ["PatientAddress", "InstitutionName", "DeviceSerialNumber", "OperatorsName"]:
        assert tag not in clean, f"{tag} should have been removed"
    assert clean.PatientBirthDate == ""  # emptied
    assert clean.AccessionNumber == ""

    # Provenance stamped.
    assert clean.PatientIdentityRemoved == "YES"
    assert clean.DeidentificationMethod

    # Private tag stripped.
    assert clean.private_tags_count if False else report.private_tags_removed >= 1


def test_retains_clinical_attributes():
    ds = _read(synthetic_dicom(seed=2))
    clean, report = deidentify_dataset(ds, salt="s")
    # Sex / age / modality / view kept for the model.
    assert clean.PatientSex == "M"
    assert clean.PatientAge == "045Y"
    assert clean.Modality == "CR"
    assert "PatientSex" in report.retained


def test_pseudonym_is_deterministic_and_salt_sensitive():
    a = pseudonymize_id("MRN-1000", "salt-A")
    b = pseudonymize_id("MRN-1000", "salt-A")
    c = pseudonymize_id("MRN-1000", "salt-B")
    assert a == b           # deterministic for the same salt
    assert a != c           # different salt → different pseudonym
    assert a.startswith("ANON-")


def test_uid_regenerated_consistently():
    raw = synthetic_dicom(seed=3)
    c1, _ = deidentify_dataset(_read(raw), salt="k")
    c2, _ = deidentify_dataset(_read(raw), salt="k")
    original = _read(raw).StudyInstanceUID
    assert c1.StudyInstanceUID != original           # linkage broken
    assert c1.StudyInstanceUID == c2.StudyInstanceUID  # but consistent


def test_pipeline_produces_png_and_clean_dicom():
    from PIL import Image

    res = process_dicom(synthetic_dicom(seed=4, rows=32, cols=32), salt="k", image_size=224)
    assert res.png_bytes and res.png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    # width/height describe the SOURCE image; the PNG is resized to image_size.
    assert res.width == 32 and res.height == 32
    assert Image.open(io.BytesIO(res.png_bytes)).size == (224, 224)
    assert res.pseudo_patient_id.startswith("ANON-")

    # The emitted DICOM must itself be de-identified.
    clean = _read(res.dicom_bytes)
    assert clean.PatientIdentityRemoved == "YES"
    assert "PatientName" not in clean or str(clean.PatientName).startswith("ANON-")
    for tag in ["PatientAddress", "InstitutionName", "DeviceSerialNumber"]:
        assert tag not in clean
