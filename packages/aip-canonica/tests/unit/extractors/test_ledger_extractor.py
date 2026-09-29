"""Unit tests for TabularLedgerExtractor."""

from decimal import Decimal
from pathlib import Path

from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor
from aip_canonica.models.ledger import EntryDirection
from aip_canonica.parsers.csv_parser import CsvParser


def test_matches_ledger_workbook(sample_ledger_csv: Path, sample_invoice_csv: Path):
    extractor = TabularLedgerExtractor()
    parser = CsvParser()

    ledger_workbook = parser.parse(sample_ledger_csv)
    invoice_workbook = parser.parse(sample_invoice_csv)

    assert extractor.matches(ledger_workbook) is True
    assert extractor.matches(invoice_workbook) is False


def test_extract_ledger_data(sample_ledger_csv: Path):
    extractor = TabularLedgerExtractor()
    workbook = CsvParser().parse(sample_ledger_csv)

    ledger = extractor.extract(workbook, source_name=str(sample_ledger_csv))

    assert "Consulting Revenue" in ledger.name
    assert ledger.party is not None
    assert "Global Clients" in ledger.party.name

    assert ledger.opening_balance == Decimal("100000.00")
    assert ledger.closing_balance == Decimal("150000.00")

    assert len(ledger.entries) == 3
    assert ledger.entries[0].amount == Decimal("25000.00")
    assert ledger.entries[0].direction == EntryDirection.CREDIT
    assert ledger.entries[2].amount == Decimal("10000.00")
    assert ledger.entries[2].direction == EntryDirection.DEBIT

    assert ledger.validate().is_valid