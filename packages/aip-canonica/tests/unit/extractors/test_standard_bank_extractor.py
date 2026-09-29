"""Unit tests for StandardBankStatementExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.models.base import TransactionDirection
from aip_canonica.parsers.csv_parser import CsvParser


def test_standard_bank_extractor_matching(
    standard_bank_statement_csv: Path, sample_invoice_csv: Path
):
    """Test that extractor correctly identifies bank statements and rejects invoices."""
    extractor = StandardBankStatementExtractor()
    parser = CsvParser()

    bank_workbook = parser.parse(standard_bank_statement_csv)
    invoice_workbook = parser.parse(sample_invoice_csv)

    assert extractor.matches(bank_workbook) is True, "Should match valid bank statement"
    assert extractor.matches(invoice_workbook) is False, "Should not match invoice"


def test_standard_bank_extractor_extraction(standard_bank_statement_csv: Path):
    """Test that extractor correctly parses bank statement data."""
    extractor = StandardBankStatementExtractor()
    workbook = CsvParser().parse(standard_bank_statement_csv)

    statement = extractor.extract(workbook, source_name=str(standard_bank_statement_csv))

    # Verify account information
    assert statement.account is not None
    assert statement.account.account_number == "9876543210", "Account number should be correct"

    # Verify holder information
    assert statement.holder is not None
    assert statement.holder.name == "Acme Enterprises", "Holder name should be correct"

    # Verify balance information
    assert statement.opening_balance == Decimal("50000.00"), "Opening balance should be correct"
    assert statement.closing_balance == Decimal("64400.00"), "Closing balance should be correct"

    # Verify transaction count and details
    assert len(statement.transactions) == 4, "Should have 4 transactions"

    # First transaction: 15000.00 Credit
    assert statement.transactions[0].amount == Decimal("15000.00"), "First transaction amount should be correct"
    assert statement.transactions[0].direction == TransactionDirection.CREDIT, "First transaction direction should be credit"
    assert statement.transactions[0].balance == Decimal("65000.00"), "First transaction balance should be correct"

    # Second transaction: 3200.00 Debit
    assert statement.transactions[1].amount == Decimal("3200.00"), "Second transaction amount should be correct"
    assert statement.transactions[1].direction == TransactionDirection.DEBIT, "Second transaction direction should be debit"

    # Validate statement
    val = statement.validate()
    assert val.is_valid, "Statement validation should succeed"