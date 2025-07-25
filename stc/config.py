"""Global configuration and paths for the semantic toolchain."""

from pathlib import Path
from typing import Optional
import os

# Default paths
DEFAULT_BUILD_DIR = Path("build")
DEFAULT_DATA_DIR = Path("data")
DEFAULT_MODELS_DIR = Path("models")
DEFAULT_TESTS_DIR = Path("tests")

# Environment variables
STC_BUILD_DIR = os.getenv("STC_BUILD_DIR")
STC_DATA_DIR = os.getenv("STC_DATA_DIR")
STC_MODELS_DIR = os.getenv("STC_MODELS_DIR")
STC_TESTS_DIR = os.getenv("STC_TESTS_DIR")

def get_build_dir() -> Path:
    """Get the build directory path."""
    if STC_BUILD_DIR:
        return Path(STC_BUILD_DIR)
    return DEFAULT_BUILD_DIR

def get_data_dir() -> Path:
    """Get the data directory path."""
    if STC_DATA_DIR:
        return Path(STC_DATA_DIR)
    return DEFAULT_DATA_DIR

def get_models_dir() -> Path:
    """Get the models directory path."""
    if STC_MODELS_DIR:
        return Path(STC_MODELS_DIR)
    return DEFAULT_MODELS_DIR

def get_tests_dir() -> Path:
    """Get the tests directory path."""
    if STC_TESTS_DIR:
        return Path(STC_TESTS_DIR)
    return DEFAULT_TESTS_DIR

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path 