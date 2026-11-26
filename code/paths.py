"""Path resolution for this release.

All scripts in this repository resolve their inputs through this module so that
nothing depends on the original authoring machine's absolute paths.

Order of precedence
-------------------
1. Environment variable ``JV_DATA_ROOT`` (points at a directory laid out like
   this repository's ``data/`` and ``models/`` folders, e.g. after unpacking the
   release assets).
2. The repository root inferred from this file's location.
"""
import os

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CODE_DIR)


def data_root():
    """Directory containing dataset files (see docs/DATA_DICTIONARY.md)."""
    return os.environ.get("JV_DATA_ROOT", os.path.join(REPO_ROOT, "data"))


def model_dir():
    """Directory containing the frozen VAE-v6 weights and scalers."""
    return os.environ.get("JV_MODEL_ROOT", os.path.join(REPO_ROOT, "models"))


def model_file(name):
    return os.path.join(model_dir(), "vae-v6", name)


def scaler_file(name):
    return os.path.join(model_dir(), name)


def data_file(*parts):
    return os.path.join(data_root(), *parts)


def results_root():
    return os.environ.get("JV_RESULTS_ROOT", os.path.join(REPO_ROOT, "results"))
