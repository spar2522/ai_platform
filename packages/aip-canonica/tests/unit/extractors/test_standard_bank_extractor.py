"""Unit tests for StandardBankStatementExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.models.base import TransactionDirection
from aip_canonica.parsers.csv_parser import CsvParser


def test_standard_bank_extractor_matching(standard_bank_statement_csv: Path, sample_invoice_csv: Path):
    extractor = StandardBankStatementExtractor()
    parser = CsvParser()

    bank_workbook = parser.parse(standard_bank_statement_csv)
    invoice_workbook = parser.parse(sample_invoice_csv)

    assert extractor.matches(bank_workbook) is True
    assert extractor.matches(invoice_workbook) is False


def test_standard_bank_extractor_extraction(standard_bank_statement_csv: Path):
    extractor = StandardBankStatementExtractor()
    workbook = CsvParser().parse(standard_bank_statement_csv)

    statement = extractor.extract(workbook, source_name=str(standard_bank_statement_csv))

    assert statement.account is not None
    assert statement.account.account_number == "9876543210"

    assert statement.holder is not None
    assert statement.holder.name == "Acme Enterprises"

    assert statement.opening_balance == Decimal("50000.00")
    assert statement.closing_balance == Decimal("64400.00")

    assert len(statement.transactions) == 4

    # First transaction: Credit of 15000.00
    first_transaction = statement.transactions[0]
    assert first_transaction.amount == Decimal("15000.00")
    assert first_transaction.direction == TransactionDirection.CREDIT
    assert first_transaction.balance == Decimal("65000.00")

    # Second transaction: Debit of 3200.00
    second_transaction = statement.transactions[1]
    assert second_transaction.amount == Decimal("3200.00")
    assert second_transaction.direction == TransactionDirection.DEBIT

    val = statement.validate()
    assert val.is_valid


def test_standard_bank_extractor_horizontal_summary_and_reverse_order(tmp_path: Path):
    csv_content = """YES BANK Ltd.,,,Statement Of Accounts
Primary Holder :SUSHIL KUMAR,Account Number : 008063700001026
10 May 2025,Description,Withdrawals,Deposits,Running Balance
25 May 2025,Salary,0.00,30000.00,30000.00
10 May 2025,Withdrawal,5000.00,0.00,25000.00
STATEMENT SUMMARY
Opening Balance,25000.00
Closing Balance,25000.00
"""

    with open(tmp_path / "test.csv", "w") as f:
        f.write(csv_content)

    extractor = StandardBankStatementExtractor()
    workbook = CsvParser().parse(tmp_path / "test.csv")

    statement = extractor.extract(workbook, source_name=str(tmp_path / "test.csv"))

    assert statement.account is not None
    assert statement.account.account_number == "008063700001026"
    assert statement.holder is not None
    assert statement.holder.name == "SUSHIL KUMAR"

    assert statement.opening_balance == Decimal("25000.00")
    assert statement.closing_balance == Decimal("25000.00")

    assert len(statement.transactions) == 2

    # First transaction in CSV is 25 May 2025, but extractor should order by date
    first_transaction = statement.transactions[0]
    assert first_transaction.date == "10 May 2025"
    assert first_transaction.description == "Withdrawal"
    assert first_transaction.withdrawals == Decimal("5000.00")
    assert first_transaction.deposits == Decimal("0.00")
    assert first_transaction.balance == Decimal("25000.00")

    # Second transaction in CSV is 10 May 2025, but extractor should order by date
    second_transaction = statement.transactions[1]
    assert second_transaction.date == "25 May 2025"
    assert second_transaction.description == "Salary"
    assert second_transaction.withdrawals == Decimal("0.00")
    assert second_transaction.deposits == Decimal("30000.00")
    assert second_transaction.balance == Decimal("30000.00")

    val = statement.validate()
    assert val.is_valid
    assert val.metrics["discrepancy"] == "0.00"