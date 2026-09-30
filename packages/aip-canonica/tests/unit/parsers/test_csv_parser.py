"""Unit tests for CsvParser."""

from pathlib import Path
from aip_canonica.models import Sheet, Workbook
from aip_canonica.parsers.csv_parser import CsvParser


def test_parse_standard_csv(standard_bank_statement_csv: Path):
    """Test parsing a standard bank statement CSV file."""
    parser = CsvParser()
    wb = parser.parse(standard_bank_statement_csv)

    assert isinstance(wb, Workbook)
    assert len(wb.sheets) == 1
    sheet = wb.sheets[0]
    assert isinstance(sheet, Sheet)
    assert sheet.name == "standard_bank_statement"
    assert len(sheet.rows) > 0


def test_csv_cell_location_and_values(tmp_path: Path):
    """Test that cell values and locations are parsed correctly."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("Name,Age,City\nAlice,30,New York\nBob,25,Los Angeles")

    parser = CsvParser()
    sheet = parser.parse(csv_file).sheets[0]

    assert len(sheet.rows) == 3
    assert sheet.rows[0].cells[0].value == "Name"
    assert sheet.rows[0].cells[1].value == "Age"
    assert sheet.rows[0].cells[2].value == "City"
    assert sheet.rows[1].cells[0].value == "Alice"
    assert sheet.rows[1].cells[1].value == "30"
    assert sheet.rows[1].cells[2].value == "New York"
    assert sheet.rows[2].cells[0].value == "Bob"
    assert sheet.rows[2].cells[1].value == "25"
    assert sheet.rows[2].cells[2].value == "Los Angeles"


def test_csv_custom_delimiter(tmp_path: Path):
    """Test parsing CSV with a custom delimiter (semicolon)."""
    csv_file = tmp_path / "test_semicolon.csv"
    csv_file.write_text("col1;col2;col3\nval1;val2;val3")

    parser = CsvParser()
    sheet = parser.parse(csv_file).sheets[0]

    assert len(sheet.rows) == 2
    assert sheet.rows[0].cells[0].value == "col1"
    assert sheet.rows[0].cells[1].value == "col2"
    assert sheet.rows[0].cells[2].value == "col3"
    assert sheet.rows[1].cells[0].value == "val1"
    assert sheet.rows[1].cells[1].value == "val2"
    assert sheet.rows[1].cells[2].value == "val3"


def test_csv_empty_rows_and_cells(tmp_path: Path):
    """Test parsing CSV with empty rows and cells."""
    csv_file = tmp_path / "test_empty.csv"
    csv_file.write_text("A,B\n,\n1,\n\n2,3")

    parser = CsvParser()
    sheet = parser.parse(csv_file).sheets[0]

    assert len(sheet.rows) == 5
    assert sheet.rows[0].cells == [Sheet.Cell("A"), Sheet.Cell("B")]
    assert sheet.rows[1].cells == [Sheet.Cell(""), Sheet.Cell("")]
    assert sheet.rows[2].cells == [Sheet.Cell("1"), Sheet.Cell("")]
    assert sheet.rows[3].cells == []
    assert sheet.rows[4].cells == [Sheet.Cell("2"), Sheet.Cell("3")]