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
    assert isinstance(workbook, Workbook), "Parsed object must be a Workbook"
    assert len(workbook.sheets) > 0, "Workbook must contain at least one sheet"


def test_understand_bank_statement():
    csv_file = SAMPLE_DIR / "bank" / "standard_bank_statement.csv"
    doc = understand(csv_file, validate=True)
    assert isinstance(doc, BankStatement), "Parsed object must be a BankStatement"
    assert doc.account_number is not None, "BankStatement must have an account number"
    assert len(doc.transactions) > 0, "BankStatement must contain transactions"

    val = validate(doc)
    assert val.is_valid, "Validation must succeed for valid BankStatement"


def test_understand_invoice():
    csv_file = SAMPLE_DIR / "invoice" / "sample_invoice.csv"
    doc = understand(csv_file, validate=True)
    assert isinstance(doc, Invoice), "Parsed object must be an Invoice"
    assert doc.invoice_number is not None, "Invoice must have an invoice number"
    assert len(doc.line_items) > 0, "Invoice must contain line items"

    val = validate(doc)
    assert val.is_valid, "Validation must succeed for valid Invoice"