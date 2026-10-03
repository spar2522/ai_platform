from pathlib import Path
import pytest

from aip_canonica.parsers import (
    CsvParser,
    ExcelParser,
    PdfParser,
    ParserFactory,
)


@pytest.mark.parametrize("file_path, expected_parser", [
    ("statement.xlsx", ExcelParser),
    ("statement.csv", CsvParser),
    ("statement.pdf", PdfParser),
])
def test_parser_factory_selects_correct_parser(file_path, expected_parser):
    parser = ParserFactory.create(Path(file_path))
    assert isinstance(parser, expected_parser)


def test_unsupported_parser_selected():
    with pytest.raises(ValueError, match="Unsupported document type"):
        ParserFactory.create(Path("statement.unknown"))