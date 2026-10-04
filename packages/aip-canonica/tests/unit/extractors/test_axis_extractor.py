"""Unit tests for AxisBankStatementExtractor supporting both tabular and multiline layouts."""

from decimal import Decimal
from pathlib import Path
import pytest

from aip_canonica.extractors.bank.axis import AxisBankStatementExtractor
from aip_canonica.models.base import TransactionDirection
from aip_canonica.models import Cell, Row, Sheet, Workbook
from aip_canonica.parsers.excel_parser import ExcelParser
from aip_canonica.parsers.pdf_parser import PdfParser
from aip_canonica.validation.validator import BankStatementValidator


def test_axis_extractor_matching():
    extractor = AxisBankStatementExtractor()

    # Synthetic Axis sheet
    axis_sheet = Sheet(
        name="AxisSheet",
        rows=[
            Row(index=0, cells=[Cell(value="Statement of Axis Account No : 5145922811", location="A1")]),
            Row(index=1, cells=[Cell(value="IFSC Code : UTIB0005157", location="A2")]),
        ],
    )
    assert extractor.matches(Workbook(sheets=[axis_sheet])) is True

    # Generic sheet without Axis anchors
    generic_sheet = Sheet(
        name="Other",
        rows=[Row(index=0, cells=[Cell(value="Some Random Bank", location="A1")])],
    )
    assert extractor.matches(Workbook(sheets=[generic_sheet])) is False


def test_axis_extractor_synthetic_tabular():
    extractor = AxisBankStatementExtractor()
    sheet = Sheet(
        name="Sheet0",
        rows=[
            Row(index=0, cells=[Cell(value="Name :- ARPIT RATAN", location="A1")]),
            Row(index=6, cells=[Cell(value="Customer ID :- 961484265", location="A7")]),
            Row(index=7, cells=[Cell(value="IFSC Code :- UTIB0005157", location="A8")]),
            Row(
                index=15,
                cells=[
                    Cell(
                        value="Statement of Account No - 5145922811 for the period (From : 01-04-2025 To : 31-03-2026)",
                        location="A16",
                    )
                ],
            ),
            Row(
                index=17,
                cells=[
                    Cell(value="SRL NO", location="A18"),
                    Cell(value="Tran Date", location="B18"),
                    Cell(value="CHQNO", location="C18"),
                    Cell(value="PARTICULARS", location="D18"),
                    Cell(value="DR", location="E18"),
                    Cell(value="CR", location="F18"),
                    Cell(value="BAL", location="G18"),
                    Cell(value="SOL", location="H18"),
                ],
            ),
            Row(
                index=18,
                cells=[
                    Cell(value="1", location="A19"),
                    Cell(value="01-07-2025", location="B19"),
                    Cell(value="-", location="C19"),
                    Cell(value="Interest Paid", location="D19"),
                    Cell(value=None, location="E19"),
                    Cell(value="500.00", location="F19"),
                    Cell(value="10500.00", location="G19"),
                    Cell(value="5157", location="H19"),
                ],
            ),
            Row(
                index=19,
                cells=[
                    Cell(value="2", location="A20"),
                    Cell(value="02-08-2025", location="B20"),
                    Cell(value="-", location="C20"),
                    Cell(value="ATM Withdrawal", location="D20"),
                    Cell(value="2000.00", location="E20"),
                    Cell(value=None, location="F20"),
                    Cell(value="8500.00", location="G20"),
                    Cell(value="5157", location="H20"),
                ],
            ),
        ],
    )
    wb = Workbook(sheets=[sheet])
    stmt = extractor.extract(wb)

    assert stmt.account is not None
    assert stmt.account.account_number == "5145922811"
    assert stmt.opening_balance == Decimal("10000.00")
    assert stmt.closing_balance == Decimal("8500.00")
    assert len(stmt.transactions) == 2
    assert stmt.transactions[0].direction == TransactionDirection.CREDIT
    assert stmt.transactions[0].amount == Decimal("500.00")
    assert stmt.transactions[1].direction == TransactionDirection.DEBIT
    assert stmt.transactions[1].amount == Decimal("2000.00")

    validator = BankStatementValidator()
    report = validator.validate(stmt)
    assert report.is_valid is True


def test_axis_extractor_synthetic_multiline():
    extractor = AxisBankStatementExtractor()
    sheet = Sheet(
        name="Page_1",
        rows=[
            Row(index=0, cells=[Cell(value="ARPIT RATAN", location="A1")]),
            Row(index=5, cells=[Cell(value="Customer ID :961484265", location="A6")]),
            Row(index=6, cells=[Cell(value="IFSC Code :UTIB0005157", location="A7")]),
            Row(
                index=12,
                cells=[
                    Cell(
                        value="Statement of Axis Account No :5145922811 for the period (From : 01-07-2026 To : 23-09-2026)",
                        location="A13",
                    )
                ],
            ),
            Row(index=15, cells=[Cell(value="OPENING BALANCE", location="A16"), Cell(value="1000.00", location="B16")]),
            Row(
                index=16,
                cells=[
                    Cell(value="01-07-2026 Interest Credit", location="A17"),
                    Cell(value="500.00", location="B17"),
                    Cell(value="1500.00 5157", location="C17"),
                ],
            ),
            Row(index=17, cells=[Cell(value="29-07-2026", location="A18")]),
            Row(index=18, cells=[Cell(value="UPI/Payment to Merchant", location="A19")]),
            Row(
                index=19,
                cells=[Cell(value="200.00", location="A20"), Cell(value="1300.00 5157", location="B20")],
            ),
            Row(index=20, cells=[Cell(value="CLOSING BALANCE", location="A21"), Cell(value="1300.00", location="B21")]),
        ],
    )
    wb = Workbook(sheets=[sheet])
    stmt = extractor.extract(wb)

    assert stmt.account is not None
    assert stmt.account.account_number == "5145922811"
    assert stmt.opening_balance == Decimal("1000.00")
    assert stmt.closing_balance == Decimal("1300.00")
    assert len(stmt.transactions) == 2
    assert stmt.transactions[0].direction == TransactionDirection.CREDIT
    assert stmt.transactions[0].amount == Decimal("500.00")
    assert stmt.transactions[1].direction == TransactionDirection.DEBIT
    assert stmt.transactions[1].amount == Decimal("200.00")

    validator = BankStatementValidator()
    report = validator.validate(stmt)
    assert report.is_valid is True


@pytest.mark.skipif(
    not Path("/Users/arpitratan/Downloads/Axis Statement.pdf").exists(),
    reason="Local Axis Statement.pdf not present",
)
def test_axis_extractor_real_pdf():
    extractor = AxisBankStatementExtractor()
    parser = PdfParser()
    wb = parser.parse(Path("/Users/arpitratan/Downloads/Axis Statement.pdf"))

    assert extractor.matches(wb) is True
    stmt = extractor.extract(wb)

    assert stmt.account is not None
    assert stmt.account.account_number == "5145922811"
    assert stmt.opening_balance == Decimal("164836.16")
    assert stmt.closing_balance == Decimal("164967.16")
    assert len(stmt.transactions) == 11

    validator = BankStatementValidator()
    report = validator.validate(stmt)
    assert report.is_valid is True
    assert report.metrics.get("discrepancy") == "0.00"


@pytest.mark.skipif(
    not Path("/Users/arpitratan/Desktop/IT returns 2025-2026/Axis SB Statement.xls").exists(),
    reason="Local Axis SB Statement.xls not present",
)
def test_axis_extractor_real_xls():
    extractor = AxisBankStatementExtractor()
    parser = ExcelParser()
    wb = parser.parse(Path("/Users/arpitratan/Desktop/IT returns 2025-2026/Axis SB Statement.xls"))

    assert extractor.matches(wb) is True
    stmt = extractor.extract(wb)

    assert stmt.account is not None
    assert stmt.account.account_number == "5145922811"
    assert stmt.opening_balance == Decimal("109706.16")
    assert stmt.closing_balance == Decimal("154836.16")
    assert len(stmt.transactions) == 22

    validator = BankStatementValidator()
    report = validator.validate(stmt)
    assert report.is_valid is True
    assert report.metrics.get("discrepancy") == "0.00"
