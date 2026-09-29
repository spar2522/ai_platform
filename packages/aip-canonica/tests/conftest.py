"""Shared pytest fixtures for Canonica tests."""

from pathlib import Path
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = PACKAGE_ROOT / "samples"


@pytest.fixture
def samples_dir() -> Path:
    """Returns the directory path containing all test samples."""
    return SAMPLES


@pytest.fixture
def simple_workbook() -> Path:
    """Returns the path to a simple workbook used for testing."""
    return SAMPLES / "fake" / "parser" / "simple.xlsx"


@pytest.fixture
def empty_rows_workbook() -> Path:
    """Returns the path to a workbook with empty rows for testing."""
    return SAMPLES / "fake" / "parser" / "empty_rows.xlsx"


@pytest.fixture
def icici_statement_path() -> Path:
    """Returns the path to a real ICICI bank statement workbook."""
    return SAMPLES / "real" / "bank" / "icici_bank_statement.xlsx"


@pytest.fixture
def standard_bank_statement_csv() -> Path:
    """Returns the path to a standard bank statement CSV file."""
    return SAMPLES / "fake" / "bank" / "standard_bank_statement.csv"


@pytest.fixture
def sample_invoice_csv() -> Path:
    """Returns the path to a sample invoice CSV file."""
    return SAMPLES / "fake" / "invoice" / "sample_invoice.csv"


@pytest.fixture
def sample_invoice_xlsx() -> Path:
    """Returns the path to a sample invoice XLSX file."""
    return SAMPLES / "fake" / "invoice" / "sample_invoice.xlsx"


@pytest.fixture
def sample_ledger_csv() -> Path:
    """Returns the path to a sample ledger CSV file."""
    return SAMPLES / "fake" / "ledger" / "sample_ledger.csv"