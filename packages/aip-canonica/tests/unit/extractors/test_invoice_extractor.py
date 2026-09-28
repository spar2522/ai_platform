"""Unit tests for TabularInvoiceExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.invoice.tabular import TabularInvoiceExtractor
from aip_canonica.parsers.csv_parser import CsvParser
from aip_canonica.parsers.excel_parser import ExcelParser


def test_invoice_extractor_matching(sample_invoice_csv: Path, standard_bank_statement_csv: Path):
    extractor = TabularInvoiceExtractor()
    parser = CsvParser()

    inv_wb = parser.parse(sample_invoice_csv)
    bank_wb = parser.parse(standard_bank_statement_csv)

    assert extractor.matches(inv_wb) is True
    assert extractor.matches(bank_wb) is False


def test_invoice_extractor_csv_extraction(sample_invoice_csv: Path):
    extractor = TabularInvoiceExtractor()
    wb = CsvParser().parse(sample_invoice_csv)

    invoice = extractor.extract(wb, source_name=str(sample_invoice_csv))

    assert invoice.invoice_number == "INV-2026-0042"
    assert invoice.invoice_date == "2026-05-15"
    assert invoice.due_date == "2026-06-15"

    assert invoice.issuer is not None
    assert "Alpha Tech" in invoice.issuer.name
    assert invoice.issuer.tax_id == "29AABCA1234F1Z5"

    assert invoice.recipient is not None
    assert "Zeta Retailers" in invoice.recipient.name
    assert invoice.recipient.tax_id == "27AABCZ9876C1Z2"

    assert len(invoice.lines) == 3
    assert invoice.lines[0].description == "Software Engineering Services"
    assert invoice.lines[0].amount == Decimal("40000.00")

    assert invoice.subtotal == Decimal("80000.00")
    assert invoice.total_amount == Decimal("92400.00")
    assert invoice.validate().is_valid


def test_invoice_extractor_excel_extraction(sample_invoice_xlsx: Path):
    extractor = TabularInvoiceExtractor()
    wb = ExcelParser().parse(sample_invoice_xlsx)

    invoice = extractor.extract(wb, source_name=str(sample_invoice_xlsx))

    assert invoice.invoice_number == "INV-2026-0099"
    assert invoice.total_amount == Decimal("17200.0")
    assert len(invoice.lines) == 2
    assert invoice.validate().is_valid
