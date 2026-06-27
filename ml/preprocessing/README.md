# DICOM preprocessing & de-identification (PHI removal)

Pipeline: **read DICOM → de-identify (remove PHI) → window to 8-bit → model-ready
transforms**. Runs both as a CLI (batch dataset ingestion) and inline from the
backend on every upload, so PHI never reaches disk.

```
ml/preprocessing/
├── deident.py      # PHI removal (PS3.15 basic confidentiality profile, pragmatic subset)
├── windowing.py    # Modality LUT (rescale) + VOI LUT (window/level) → 8-bit
├── transforms.py   # MONAI transforms (eval + train augmentation) with numpy fallback
├── pipeline.py     # end-to-end: process_dicom() / process_directory()
├── synthetic.py    # synthetic DICOMs with FAKE PHI (demos/tests only)
└── __main__.py     # CLI
```

## What de-identification does

- **Direct identifiers** — `PatientName`, `PatientID` → deterministic pseudonym
  (`ANON-…`, salted SHA-256, non-reversible); address/phone/institution/physician/
  device serial → removed; birth date, accession, study dates/times → emptied.
- **UIDs** (`StudyInstanceUID`, `SeriesInstanceUID`, `SOPInstanceUID`, …) →
  consistently regenerated under the `2.25` root, so relationships survive but
  linkage to the original is broken.
- **Private tags** and **overlay/curve groups** (`0x50xx`/`0x60xx`) → stripped
  (can hide burned-in PHI / vendor blobs).
- **Provenance** → stamps `PatientIdentityRemoved=YES` + `DeidentificationMethod`.
- **Retained on purpose** (clinically useful, low-risk): `PatientSex`,
  `PatientAge`, `Modality`, `ViewPosition`, `BodyPartExamined`, pixel-calibration
  tags. Tune in `deident.DEFAULT_POLICY`.

`BurnedInAnnotation=YES` is **flagged** (pixel text may contain PHI) but not
OCR-redacted — that's out of scope for metadata de-identification.

## CLI

```bash
pip install pydicom numpy pillow          # (monai optional, for transforms)

# Make a synthetic DICOM with fake PHI to experiment with
python -m ml.preprocessing --make-sample sample.dcm

# De-identify one file → PNG + de-identified DICOM + JSON report
python -m ml.preprocessing --in sample.dcm --out-dir ./clean --salt "$DEIDENT_SALT"

# Batch a whole folder (writes PNGs + manifest.csv)
python -m ml.preprocessing --in-dir ./raw_dicom --out-dir ./clean --salt "$DEIDENT_SALT"
```

## Used by the backend

`backend/app/services/study_service.create_study` calls `process_dicom()` for
every `.dcm` upload **before writing to disk**. If a file can't be parsed/
de-identified the upload is rejected with HTTP 422 (never persisted), and a
`study.deidentify` entry — with the summary of what was removed — is written to
the audit trail. The salt comes from `DEIDENT_SALT` (keep it secret; the same
salt yields stable pseudonyms across studies of the same patient).

## Tests

`ml/tests/test_preprocessing.py` proves PHI is removed/pseudonymized, clinical
attributes are retained, pseudonyms are deterministic + salt-sensitive, UIDs are
consistently regenerated, and the pipeline emits a valid PNG + de-identified
DICOM. All run on synthetic data — no real DICOM dataset required.
