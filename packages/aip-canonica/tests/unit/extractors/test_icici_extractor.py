"""Unit tests for ICICIBankStatementExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.bank.icici import ICICIBankStatementExtractor
from aip_canonica.models.base import TransactionDirection
from aip_canonica.parsers.excel_parser import ExcelParser


def test_icici_extractor_matching(icici_statement_path: Path, simple_workbook: Path):
    """Test that the extractor correctly identifies ICICI workbooks and rejects others."""
    extractor = ICICIBankStatementExtractor()
    parser = ExcelParser()

    icici_workbook = parser.parse(icici_statement_path)
    non_icici_workbook = parser.parse(simple_workbook)

    assert extractor.matches(icici_workbook) is True
    assert extractor.matches(non_icici_workbook) is False


def test_icici_extractor_extraction_real_statement(icici_statement_path: Path):
    """Test the extraction process on a real ICICI statement, verifying all metadata and transactions."""
    extractor = ICICIBankStatementExtractor()
    parser = ExcelParser()
    icici_workbook = parser.parse(icici_statement_path)

    statement = extractor.extract(icici_workbook, source_name=str(icici_statement_path))

    # Account metadata
    assert statement.account is not None
    assert statement.account.account_number == "114905501033"
    assert statement.account.ifsc_code == "ICIC0001149"
    assert statement.account.institution_name == "ICICI Bank Ltd."

    # Holder metadata
    assert statement.holder is not None
    assert "SHREE KRISHNA ENTERPRISES" in statement.holder.name

    # Institution
    assert statement.institution is not None
    assert statement.institution.name == "ICICI Bank Ltd."

    # Balances
    assert statement.opening_balance == Decimal("-15192804.00")
    assert statement.closing_balance == Decimal("-23519519.07")

    # Transactions count
    assert len(statement.transactions) == 1518

    # First transaction
    first = statement.transactions[0]
    assert first.direction == TransactionDirection.CREDIT
    assert first.amount == Decimal("3348.00")
    assert first.provenance is not None
    assert first.provenance.sheet == "Sheet0"
    assert first.provenance.row == 18

    # Counterparty extracted from remarks
    assert first.counterparty is not None
    assert first.counterparty.name == "ANKIT KUMA"

    # Validation
    assert statement.validate() is None