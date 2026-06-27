"""Build synthetic DICOM files carrying fake PHI — for demos and tests only.

Never contains real patient data; lets us exercise the de-identification and
windowing pipeline end-to-end without shipping any DICOM dataset.
"""
from __future__ import annotations

import io

import numpy as np


def synthetic_dicom(seed: int = 0, rows: int = 32, cols: int = 32, *, with_phi: bool = True) -> bytes:
    """Return DICOM bytes with pixel data and (optionally) populated PHI tags."""
    import pydicom
    from pydicom.dataset import FileDataset, FileMetaDataset
    from pydicom.uid import generate_uid, ExplicitVRLittleEndian, SecondaryCaptureImageStorage

    fm = FileMetaDataset()
    fm.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    fm.MediaStorageSOPInstanceUID = generate_uid()
    fm.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=fm, preamble=b"\0" * 128)
    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = fm.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()

    if with_phi:
        ds.PatientName = "Doe^John"
        ds.PatientID = f"MRN-{1000 + seed}"
        ds.PatientBirthDate = "19800101"
        ds.PatientAddress = "123 Main St"
        ds.InstitutionName = "General Hospital"
        ds.ReferringPhysicianName = "House^Gregory"
        ds.OperatorsName = "Tech^A"
        ds.AccessionNumber = f"ACC{seed:05d}"
        ds.StudyDate = "20260101"
        ds.StudyTime = "120000"
        ds.DeviceSerialNumber = "SN-ABC-123"
        # A private tag that could hide PHI.
        ds.add_new(0x00091001, "LO", "vendor-private-blob")

    # Clinically useful attributes we intend to retain.
    ds.PatientSex = "M"
    ds.PatientAge = "045Y"
    ds.Modality = "CR"
    ds.ViewPosition = "PA"
    ds.BodyPartExamined = "CHEST"

    # Image module — a simple gradient with a bright square (a "lesion").
    img = np.tile(np.linspace(0, 4095, cols, dtype=np.uint16), (rows, 1))
    img[rows // 4: rows // 2, cols // 4: cols // 2] = 4095
    ds.Rows, ds.Columns = rows, cols
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0
    ds.RescaleSlope = 1
    ds.RescaleIntercept = 0
    ds.WindowCenter = 2048
    ds.WindowWidth = 4096
    ds.PixelData = img.tobytes()

    # Encoding is derived from the Explicit VR Little Endian transfer syntax set
    # in file_meta (the is_little_endian / is_implicit_VR flags are deprecated).
    buf = io.BytesIO()
    ds.save_as(buf, little_endian=True, implicit_vr=False)
    return buf.getvalue()
