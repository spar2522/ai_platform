from pathlib import Path

from aip_canonica.internal.parsers import (
    CsvParser,
    ExcelParser,
    ParserFactory,
)


def test_excel_parser_selected():

    parser = ParserFactory.create(Path("statement.xlsx"))

    assert isinstance(parser, ExcelParser)


def test_csv_parser_selected():

    parser = ParserFactory.create(Path("statement.csv"))

    assert isinstance(parser, CsvParser)
