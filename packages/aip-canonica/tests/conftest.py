from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

SAMPLES = PACKAGE_ROOT / "samples"


@pytest.fixture
def simple_workbook():
    return SAMPLES / "fake" / "parser" / "simple.xlsx"


@pytest.fixture
def empty_rows_workbook():
    return SAMPLES / "fake" / "parser" / "empty_rows.xlsx"
