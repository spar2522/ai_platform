from pathlib import Path

from aip_canonica import (
    BankStatement,
    Invoice,
    Workbook,
    parse_document,
    understand,
    validate,
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "samples" / "fake"


def test_parse_document_returns_workbook():
    csv_file = SAMPLE_DIR / "bank" / "standard_bank_statement.csv"
    workbook = parse_document(csv_file)
    assert isinstance(workbook, Workbook)
    assert len(workbook.sheets) > 0


def test_understand_bank_statement():
    csv_file = SAMPLE_DIR / "bank" / "standard_bank_statement.csv"
    doc = understand(csv_file, validate=True)
    assert isinstance(doc, BankStatement)
    assert doc.account_number is not None
    assert len(doc.transactions) > 0

    val = validate(doc)
    assert val.is_valid


def test_understand_invoice():
    csv_file = SAMPLE_DIR / "invoice" / "sample_invoice.csv"
    doc = understand(csv_file, validate=True)
    assert isinstance(doc, Invoice)
    assert doc.invoice_number is not None
    assert len(doc.line_items) > 0

    val = validate(doc)
    assert val.is_valid
