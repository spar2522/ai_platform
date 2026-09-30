from pathlib import Path
import pytest

from aip_canonica.parsers import (
    CsvParser,
    ExcelParser,
    ParserFactory,
    PdfParser,
)


def test_excel_parser_selected():
    parser = ParserFactory.create(Path("statement.xlsx"))
    assert isinstance(parser, ExcelParser)


def test_csv_parser_selected():
    parser = ParserFactory.create(Path("statement.csv"))
    assert isinstance(parser, CsvParser)


def test_pdf_parser_selected():
    parser = ParserFactory.create(Path("statement.pdf"))
    assert isinstance(parser, PdfParser)


def test_unsupported_parser_selected():
    with pytest.raises(ValueError, match="Unsupported document type"):
        ParserFactory.create(Path("statement.unknown"))