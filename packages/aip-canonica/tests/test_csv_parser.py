import pytest

from aip_canonica.internal.parsers import CsvParser


def test_csv_parser_not_implemented():

    parser = CsvParser()

    with pytest.raises(NotImplementedError):
        parser.parse("dummy.csv")
