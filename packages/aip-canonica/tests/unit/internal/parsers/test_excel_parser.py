from aip_canonica.internal.models import Workbook, Sheet
from aip_canonica.internal.parsers import ExcelParser


def test_parse_returns_workbook(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    assert isinstance(workbook, Workbook)


def test_parse_creates_sheet(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    assert len(workbook.sheets) == 1
    assert isinstance(workbook.sheets[0], Sheet)


def test_sheet_name_is_preserved(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    assert workbook.sheets[0].name == "Sheet1"


def test_rows_are_loaded(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    assert len(workbook.sheets[0].rows) == 3


def test_cells_are_loaded(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    assert len(workbook.sheets[0].rows[0].cells) == 3


def test_cell_value_is_preserved(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    cell = workbook.sheets[0].rows[1].cells[0]

    assert cell.value == "Alice"


def test_cell_location_is_preserved(simple_workbook):
    workbook = ExcelParser().parse(simple_workbook)

    cell = workbook.sheets[0].rows[1].cells[0]

    assert cell.location.address == "A2"
    assert cell.location.row == 2
    assert cell.location.column == 1


def test_preserves_empty_rows(empty_rows_workbook):
    workbook = ExcelParser().parse(empty_rows_workbook)

    assert len(workbook.sheets[0].rows) == 5
