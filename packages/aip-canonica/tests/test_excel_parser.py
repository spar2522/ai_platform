import pytest

from aip_canonica.internal.parsers import ExcelParser


def test_excel_parser_not_implemented():

    parser = ExcelParser()

    with pytest.raises(NotImplementedError):
        parser.parse("dummy.xlsx")
