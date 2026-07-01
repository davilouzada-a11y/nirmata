"""Real labeled chest X-rays from the public covid-chestxray-dataset.

Source: https://github.com/ieee8023/covid-chestxray-dataset (GitHub, reachable).

We use it because it's real radiographs with real labels that we can fetch here.
Its labels are diagnosis-centric and heavily pneumonia/COVID, with few normals,
so it supports validating **pneumonia/consolidation detection** and
**abnormal-vs-normal triage** — NOT pneumothorax/effusion/cardiomegaly (unlabeled
here). See the validation README for the honest caveats.
"""
from __future__ import annotations

import os
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/ieee8023/covid-chestxray-dataset/master"
META_URL = f"{RAW_BASE}/metadata.csv"
IMG_BASE = f"{RAW_BASE}/images"

FRONTAL_VIEWS = {"PA", "AP", "AP Supine", "AP Erect"}


def _download(url: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    # urllib honors HTTPS_PROXY from the environment.
    with urllib.request.urlopen(url, timeout=60) as r:
        data = r.read()
    with open(dest, "wb") as fh:
        fh.write(data)


def load_samples(cache_dir: str, *, limit_pos: int = 60, limit_neg: int | None = None,
                 seed: int = 0) -> list[dict]:
    """Return [{image_path, labels:{pneumonia, normal}}] for frontal X-rays.

    Positives = any `Pneumonia*` finding; negatives = `No Finding`.
    """
    import pandas as pd

    os.makedirs(cache_dir, exist_ok=True)
    meta_path = os.path.join(cache_dir, "metadata.csv")
    _download(META_URL, meta_path)
    df = pd.read_csv(meta_path)

    df = df[(df["modality"] == "X-ray") & (df["view"].isin(FRONTAL_VIEWS))].copy()
    df = df.dropna(subset=["filename"])
    df["is_pneumonia"] = df["finding"].str.startswith("Pneumonia")
    df["is_normal"] = df["finding"] == "No Finding"

    pos = df[df["is_pneumonia"]].sample(frac=1.0, random_state=seed).head(limit_pos)
    neg = df[df["is_normal"]]
    if limit_neg:
        neg = neg.sample(frac=1.0, random_state=seed).head(limit_neg)

    samples = []
    for _, row in pd.concat([pos, neg]).iterrows():
        fn = str(row["filename"])
        dest = os.path.join(cache_dir, "images", fn)
        try:
            _download(f"{IMG_BASE}/{urllib.parse.quote(fn)}", dest)
        except Exception:
            continue  # skip files that 404 / fail
        samples.append({
            "image_path": dest,
            "finding": row["finding"],
            "labels": {
                "pneumonia": 1 if row["is_pneumonia"] else 0,
                "normal": 1 if row["is_normal"] else 0,
            },
        })
    return samples
