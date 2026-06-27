"""Pytest bootstrap: make the sibling ``ml/`` package importable during tests
(the backend lives in a subdir; ``ml/`` is one level up)."""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
