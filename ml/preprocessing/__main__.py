"""CLI for the DICOM preprocessing / de-identification pipeline.

    # single file → de-identified PNG + DICOM + JSON report
    python -m ml.preprocessing --in study.dcm --out-dir ./clean

    # batch a directory
    python -m ml.preprocessing --in-dir ./raw --out-dir ./clean

    # generate a synthetic DICOM (with fake PHI) to try it out
    python -m ml.preprocessing --make-sample sample.dcm
"""
from __future__ import annotations

import argparse
import json
import os

from ml.preprocessing.pipeline import process_dicom, process_directory


def main():
    ap = argparse.ArgumentParser(description="DICOM de-identification + preprocessing")
    ap.add_argument("--in", dest="infile", help="single DICOM file")
    ap.add_argument("--in-dir", dest="indir", help="directory of DICOM files")
    ap.add_argument("--out-dir", dest="outdir", default="./clean")
    ap.add_argument("--salt", default="nirmata", help="pseudonymization salt (keep secret)")
    ap.add_argument("--image-size", type=int, default=512)
    ap.add_argument("--make-sample", help="write a synthetic DICOM (fake PHI) to this path and exit")
    args = ap.parse_args()

    if args.make_sample:
        from ml.preprocessing.synthetic import synthetic_dicom
        with open(args.make_sample, "wb") as fh:
            fh.write(synthetic_dicom(seed=1))
        print(f"Wrote synthetic DICOM with fake PHI → {args.make_sample}")
        return

    if args.indir:
        rows = process_directory(args.indir, args.outdir, salt=args.salt)
        ok = [r for r in rows if "error" not in r]
        print(f"Processed {len(ok)}/{len(rows)} files → {args.outdir}/ (see manifest.csv)")
        return

    if args.infile:
        os.makedirs(args.outdir, exist_ok=True)
        res = process_dicom(args.infile, salt=args.salt, image_size=args.image_size)
        base = os.path.splitext(os.path.basename(args.infile))[0]
        with open(os.path.join(args.outdir, base + ".png"), "wb") as fh:
            fh.write(res.png_bytes)
        with open(os.path.join(args.outdir, base + ".deident.dcm"), "wb") as fh:
            fh.write(res.dicom_bytes)
        report = {
            "pseudo_patient_id": res.pseudo_patient_id,
            "size": [res.width, res.height],
            "deident": res.deident,
            "warnings": res.warnings,
        }
        with open(os.path.join(args.outdir, base + ".report.json"), "w") as fh:
            json.dump(report, fh, indent=2)
        print(json.dumps(report, indent=2))
        return

    ap.error("provide --in, --in-dir, or --make-sample")


if __name__ == "__main__":
    main()
