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

    assert extractor.matches(bank_wb) is True
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

    val = statement.validate()
    assert val.is_valid


def test_standard_bank_extractor_horizontal_summary_and_reverse_order(tmp_path: Path):
    csv_content = """YES BANK Ltd.,,,Statement Of Accounts
Primary Holder :SUSHIL KUMAR DROLIA, A/C Opening Date :22/09/2020
Account No :008063700001026 (CURRENT)
RTGS/NEFT/ IFSC :YESB0000080

Transaction Date,Value Date,Cheque No/Reference No,Description,Withdrawals,Deposits,Running Balance
25 May 2026,25 May 2026,REF1,Supplier Payment A,5000.00,,45000.00
10 May 2026,10 May 2026,REF2,Customer Settlement,,10000.00,50000.00

STATEMENT SUMMARY :-
Opening Balance,,Total Withdrawals,,Total Deposits,,Closing Balance
40000.00,,5000.00,,10000.00,,45000.00
"""
    f = tmp_path / "yes_bank_test.csv"
    f.write_text(csv_content)

    extractor = StandardBankStatementExtractor()
    wb = CsvParser().parse(f)

    assert extractor.matches(wb) is True
    statement = extractor.extract(wb, source_name=str(f))

    assert statement.account is not None
    assert statement.account.account_number == "008063700001026"
    assert statement.holder is not None
    assert statement.holder.name == "SUSHIL KUMAR DROLIA"
    assert statement.opening_balance == Decimal("40000.00")
    assert statement.closing_balance == Decimal("45000.00")
    assert len(statement.transactions) == 2
    assert statement.transactions[0].date == "25 May 2026"
    assert statement.transactions[0].amount == Decimal("5000.00")
    assert statement.transactions[0].direction == TransactionDirection.DEBIT

    assert statement.transactions[1].date == "10 May 2026"
    assert statement.transactions[1].amount == Decimal("10000.00")
    assert statement.transactions[1].direction == TransactionDirection.CREDIT

    val = statement.validate()
    assert val.is_valid
    assert val.metrics["discrepancy"] == "0.00"

