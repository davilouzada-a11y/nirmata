"""End-to-end DICOM preprocessing pipeline.

    read DICOM → de-identify (PHI removal) → window to 8-bit → (optional) save a
    de-identified DICOM + a display PNG → report.

Designed to run both as a CLI (batch ingestion of a dataset) and inline from the
backend on upload, so no PHI is ever persisted.
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass, field

from ml.preprocessing.deident import deidentify_dataset
from ml.preprocessing.windowing import to_display_uint8


@dataclass
class ProcessResult:
    pseudo_patient_id: str
    width: int
    height: int
    deident: dict
    burned_in_annotation_flag: bool = False
    warnings: list[str] = field(default_factory=list)
    png_bytes: bytes | None = None
    dicom_bytes: bytes | None = None


def _read_dicom(source):
    import pydicom

    if isinstance(source, (bytes, bytearray)):
        return pydicom.dcmread(io.BytesIO(source), force=True)
    return pydicom.dcmread(source, force=True)


def process_dicom(source, *, salt: str = "nirmata", image_size: int | None = 512,
                  want_png: bool = True, want_dicom: bool = True) -> ProcessResult:
    """De-identify and render a single DICOM (path or bytes)."""
    from PIL import Image

    ds = _read_dicom(source)

    # Flag possible burned-in pixel text BEFORE we drop the tag, so reviewers know
    # to OCR-redact (out of scope for metadata de-id).
    burned = str(getattr(ds, "BurnedInAnnotation", "")).upper() == "YES"

    clean, report = deidentify_dataset(ds, salt=salt)

    display = to_display_uint8(clean)  # HxW uint8
    height, width = display.shape[:2]

    result = ProcessResult(
        pseudo_patient_id=report.pseudo_patient_id,
        width=width, height=height,
        deident=report.summary(),
        burned_in_annotation_flag=burned,
    )
    if burned:
        result.warnings.append("BurnedInAnnotation=YES — pixel text may contain PHI; OCR review advised.")

    if want_png:
        img = Image.fromarray(display, "L")
        if image_size:
            img = img.resize((image_size, image_size), Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result.png_bytes = buf.getvalue()

    if want_dicom:
        buf = io.BytesIO()
        ts = getattr(getattr(clean, "file_meta", None), "TransferSyntaxUID", None)
        if ts is not None:
            clean.save_as(buf, little_endian=ts.is_little_endian, implicit_vr=ts.is_implicit_VR)
        else:
            clean.save_as(buf, little_endian=True, implicit_vr=False)
        result.dicom_bytes = buf.getvalue()

    return result


def process_directory(in_dir: str, out_dir: str, *, salt: str = "nirmata") -> list[dict]:
    """Batch-process a folder of .dcm files; writes PNGs + a manifest, returns rows."""
    import csv

    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for name in sorted(os.listdir(in_dir)):
        if not name.lower().endswith((".dcm", ".dicom")):
            continue
        path = os.path.join(in_dir, name)
        try:
            res = process_dicom(path, salt=salt, want_dicom=False)
            out_png = os.path.join(out_dir, os.path.splitext(name)[0] + ".png")
            with open(out_png, "wb") as fh:
                fh.write(res.png_bytes)
            rows.append({
                "source": name, "png": os.path.basename(out_png),
                "pseudo_patient_id": res.pseudo_patient_id,
                "attributes_cleaned": res.deident["removed_or_modified"],
                "private_tags_removed": res.deident["private_tags_removed"],
                "burned_in_flag": res.burned_in_annotation_flag,
            })
        except Exception as err:  # keep going; record the failure
            rows.append({"source": name, "error": str(err)})

    manifest = os.path.join(out_dir, "manifest.csv")
    if rows:
        keys = sorted({k for r in rows for k in r})
        with open(manifest, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    return rows
