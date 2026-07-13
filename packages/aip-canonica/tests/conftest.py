from pathlib import Path

import pytest

# Determine the root of the package by resolving the current file's parent directory
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# Define the directory containing test samples
SAMPLES_DIR = PACKAGE_ROOT / "samples"


@pytest.fixture
def simple_workbook():
    """Provides a path to a sample workbook with a simple structure."""
    path = SAMPLES_DIR / "fake" / "parser" / "simple.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Test sample file not found: {path}")
    return path


@pytest.fixture
def empty_rows_workbook():
    """Provides a path to a sample workbook with empty rows."""
    path = SAMPLES_DIR / "fake" / "parser" / "empty_rows.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Test sample file not found: {path}")
    return path