"""Make the sibling ``ml/`` package importable from the backend.

In Docker the build copies ``ml/`` next to the app; for local dev the backend is
typically run from ``backend/`` so the repo root (which contains ``ml/``) isn't on
``sys.path``. This helper adds it on demand, so de-identification and the torch
inference backend work in both setups without restructuring.
"""
from __future__ import annotations

import os
import sys


def ensure_ml_importable() -> bool:
    try:
        import ml  # noqa: F401
        return True
    except ImportError:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        try:
            import ml  # noqa: F401
            return True
        except ImportError:
            return False
