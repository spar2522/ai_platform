"""Shared pytest fixtures for Canonica tests."""

from pathlib import Path
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = PACKAGE_ROOT / "samples"


@pytest.fixture
def samples_dir() -> Path:
    return SAMPLES


@pytest.fixture
def simple_workbook() -> Path:
    return SAMPLES / "fake" / "parser" / "simple.xlsx"


@pytest.fixture
def empty_rows_workbook() -> Path:
    return SAMPLES / "fake" / "parser" / "empty_rows.xlsx"


@pytest.fixture
def icici_statement_path() -> Path:
    return SAMPLES / "real" / "bank" / "icici_bank_statement.xlsx"


@pytest.fixture
def standard_bank_statement_csv() -> Path:
    return SAMPLES / "fake" / "bank" / "standard_bank_statement.csv"


@pytest.fixture
def sample_invoice_csv() -> Path:
    return SAMPLES / "fake" / "invoice" / "sample_invoice.csv"


@pytest.fixture
def sample_invoice_xlsx() -> Path:
    return SAMPLES / "fake" / "invoice" / "sample_invoice.xlsx"


@pytest.fixture
def sample_ledger_csv() -> Path:
    return SAMPLES / "fake" / "ledger" / "sample_ledger.csv"
