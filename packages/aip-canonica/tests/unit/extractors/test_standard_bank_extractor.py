"""Unit tests for StandardBankStatementExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.models.base import TransactionDirection
from aip_canonica.parsers.csv_parser import CsvParser


def test_standard_bank_extractor_matching(standard_bank_statement_csv: Path, sample_invoice_csv: Path):
    extractor = StandardBankStatementExtractor()
    parser = CsvParser()

    bank_wb = parser.parse(standard_bank_statement_csv)
    inv_wb = parser.parse(sample_invoice_csv)

    # Bank workbook should match as it contains standard bank statement data
    assert extractor.matches(bank_wb) is True
    # Invoice CSV should not match as it contains invoice data, not bank statement
    assert extractor.matches(inv_wb) is False


def test_standard_bank_extractor_extraction(standard_bank_statement_csv: Path):
    extractor = StandardBankStatementExtractor()
    wb = CsvParser().parse(standard_bank_statement_csv)

    statement = extractor.extract(wb, source_name=str(standard_bank_statement_csv))

    assert statement.account is not None
    assert statement.account.account_number == "9876543210"

    assert statement.holder is not None
    assert statement.holder.name == "Acme Enterprises"

    assert statement.opening_balance == Decimal("50000.00")
    assert statement.closing_balance == Decimal("64400.00")

    assert len(statement.transactions) == 4
    # First txn: 15000.00 Credit
    assert statement.transactions[0].amount == Decimal("15000.00")
    assert statement.transactions[0].direction == TransactionDirection.CREDIT
    assert statement.transactions[0].balance == Decimal("65000.00")

    # Second txn: 3200.00 Debit
    assert statement.transactions[1].amount == Decimal("3200.00")
    assert statement.transactions[1].direction == TransactionDirection.DEBIT

    validation_result = statement.validate()
    assert validation_result.is_valid