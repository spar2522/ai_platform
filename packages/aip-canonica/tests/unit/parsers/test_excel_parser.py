"""Unit tests for the ExcelParser class.

These tests verify that the ExcelParser correctly parses Excel files into
Workbook and Sheet objects, preserving structure, data, and metadata.
"""

from aip_canonica.models import Workbook, Sheet
from aip_canonica.parsers import ExcelParser


def _parse_workbook(fixture):
    """Helper function to parse a fixture into a Workbook."""
    return ExcelParser().parse(fixture)


def test_parse_returns_workbook(simple_workbook):
    """Test that parsing returns a Workbook instance."""
    workbook = _parse_workbook(simple_workbook)
    assert isinstance(workbook, Workbook)


def test_parse_creates_sheet(simple_workbook):
    """Test that parsing creates a Sheet in the Workbook."""
    workbook = _parse_workbook(simple_workbook)
    assert len(workbook.sheets) == 1
    assert isinstance(workbook.sheets[0], Sheet)


def test_sheet_name_is_preserved(simple_workbook):
    """Test that the sheet name is preserved during parsing."""
    workbook = _parse_workbook(simple_workbook)
    assert workbook.sheets[0].name == "Sheet1"


def test_rows_are_loaded(simple_workbook):
    """Test that rows are correctly loaded from the sheet."""
    workbook = _parse_workbook(simple_workbook)
    assert len(workbook.sheets[0].rows) == 3


def test_cells_are_loaded(simple_workbook):
    """Test that cells are correctly loaded from the rows."""
    workbook = _parse_workbook(simple_workbook)
    assert len(workbook.sheets[0].rows[0].cells) == 3


def test_cell_value_is_preserved(simple_workbook):
    """Test that cell values are preserved during parsing."""
    workbook = _parse_workbook(simple_workbook)
    cell = workbook.sheets[0].rows[1].cells[0]
    assert cell.value == "Alice"


def test_cell_location_is_preserved(simple_workbook):
    """Test that cell locations are preserved during parsing."""
    workbook = _parse_workbook(simple_workbook)
    cell = workbook.sheets[0].rows[1].cells[0]
    assert cell.location.address == "A2"
    assert cell.location.row == 2
    assert cell.location.column == 1


def test_preserves_empty_rows(empty_rows_workbook):
    """Test that empty rows are preserved in the parsed workbook."""
    workbook = _parse_workbook(empty_rows_workbook)
    assert len(workbook.sheets[0].rows) == 5