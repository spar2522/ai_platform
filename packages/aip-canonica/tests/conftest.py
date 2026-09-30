"""Shared pytest fixtures for Canonica tests."""

from pathlib import Path
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = PACKAGE_ROOT / "samples"  # Directory containing test sample files


@pytest.fixture
def samples_dir() -> Path:
    """Return the directory containing test sample files."""
    return SAMPLES


@pytest.fixture
def simple_workbook() -> Path:
    """Provide path to a simple Excel workbook for testing."""
    return SAMPLES / "fake" / "parser" / "simple.xlsx"


@pytest.fixture
def empty_rows_workbook() -> Path:
    """Provide path to an Excel workbook with empty rows for testing."""
    return SAMPLES / "fake" / "parser" / "empty_rows.xlsx"


@pytest.fixture
def icici_statement_path() -> Path:
    """Provide path to a real ICICI bank statement Excel file."""
    return SAMPLES / "real" / "bank" / "icici_bank_statement.xlsx"


@pytest.fixture
def standard_bank_statement_csv() -> Path:
    """Provide path to a standard bank statement CSV file."""
    return SAMPLES / "fake" / "bank" / "standard_bank_statement.csv"


@pytest.fixture
def sample_invoice_csv() -> Path:
    """Provide path to a sample invoice CSV file."""
    return SAMPLES / "fake" / "invoice" / "sample_invoice.csv"


@pytest.fixture
def sample_invoice_xlsx() -> Path:
    """Provide path to a sample invoice Excel file."""
    return SAMPLES / "fake" / "invoice" / "sample_invoice.xlsx"


@pytest.fixture
def sample_ledger_csv() -> Path:
    """Provide path to a sample ledger CSV file."""
    return SAMPLES / "fake" / "ledger" / "sample_ledger.csv"