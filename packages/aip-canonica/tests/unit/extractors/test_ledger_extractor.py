"""Unit tests for TabularLedgerExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor
from aip_canonica.models.ledger import EntryDirection
from aip_canonica.parsers.csv_parser import CsvParser


def test_ledger_extractor_matching(sample_ledger_csv: Path, sample_invoice_csv: Path):
    extractor = TabularLedgerExtractor()
    parser = CsvParser()

    ledger_workbook = parser.parse(sample_ledger_csv)
    invoice_workbook = parser.parse(sample_invoice_csv)

    assert extractor.matches(ledger_workbook) is True
    assert extractor.matches(invoice_workbook) is False


def test_ledger_extractor_extraction(sample_ledger_csv: Path):
    extractor = TabularLedgerExtractor()
    workbook = CsvParser().parse(sample_ledger_csv)

    ledger = extractor.extract(workbook, source_name=str(sample_ledger_csv))

    assert "Consulting Revenue" in ledger.name
    assert ledger.party is not None
    assert "Global Clients" in ledger.party.name

    assert ledger.opening_balance == Decimal("100000.00")
    assert ledger.closing_balance == Decimal("150000.00")

    assert len(ledger.entries) == 3
    first_entry = ledger.entries[0]
    third_entry = ledger.entries[2]
    assert first_entry.amount == Decimal("25000.00")
    assert first_entry.direction == EntryDirection.CREDIT
    assert third_entry.amount == Decimal("10000.00")
    assert third_entry.direction == EntryDirection.DEBIT

    assert ledger.validate().is_valid