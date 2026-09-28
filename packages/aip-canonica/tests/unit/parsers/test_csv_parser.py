"""Unit tests for CsvParser."""

from pathlib import Path
from aip_canonica.models import Sheet, Workbook
from aip_canonica.parsers.csv_parser import CsvParser


def test_parse_standard_csv(standard_bank_statement_csv: Path):
    parser = CsvParser()
    wb = parser.parse(standard_bank_statement_csv)

    assert isinstance(wb, Workbook)
    assert len(wb.sheets) == 1
    sheet = wb.sheets[0]
    assert isinstance(sheet, Sheet)
    assert sheet.name == "standard_bank_statement"
    assert len(sheet.rows) > 0


def test_csv_cell_location_and_values(tmp_path: Path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age,City\nAlice,30,New York\nBob,25,San Francisco\n")

    wb = CsvParser().parse(csv_file)
    sheet = wb.sheets[0]

    assert len(sheet.rows) == 3
    # Header row
    assert sheet.rows[0].cells[0].value == "Name"
    assert sheet.rows[0].cells[0].location.address == "A1"
    assert sheet.rows[0].cells[0].location.row == 1
    assert sheet.rows[0].cells[0].location.column == 1

    # Row 2
    assert sheet.rows[1].cells[0].value == "Alice"
    assert sheet.rows[1].cells[1].value == "30"
    assert sheet.rows[1].cells[2].value == "New York"
    assert sheet.rows[1].cells[2].location.address == "C2"


def test_csv_empty_rows_and_cells(tmp_path: Path):
    csv_file = tmp_path / "empty_test.csv"
    csv_file.write_text("A,B\n,\n1,\n\n2,3\n")

    wb = CsvParser().parse(csv_file)
    sheet = wb.sheets[0]

    assert len(sheet.rows) == 5
    # Row 2 is empty cells
    assert sheet.rows[1].cells[0].value == ""
    # Row 4 is completely empty line
    assert sheet.rows[3].cells == []


def test_csv_custom_delimiter(tmp_path: Path):
    csv_file = tmp_path / "semi.csv"
    csv_file.write_text("col1;col2;col3\nval1;val2;val3\n")

    wb = CsvParser().parse(csv_file)
    sheet = wb.sheets[0]

    assert len(sheet.rows) == 2
    assert sheet.rows[0].cells[0].value == "col1"
    assert sheet.rows[0].cells[1].value == "col2"


def test_csv_empty_file(tmp_path: Path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")

    wb = CsvParser().parse(csv_file)
    assert len(wb.sheets) == 1
    assert len(wb.sheets[0].rows) == 0
