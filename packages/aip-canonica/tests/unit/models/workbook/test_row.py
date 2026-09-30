from aip_canonica.models import Cell, CellLocation, Row


def test_row():
    """Test that a Row can be initialized with cells and that their properties are correctly set."""
    row = Row(index=1)
    assert row.index == 1  # Ensure the row's index is correctly set

    cell = Cell(
        value="ABC",
        location=CellLocation(
            sheet="Sheet1",
            row=1,
            column=1,
            address="A1",
        ),
    )
    row.cells.append(cell)

    assert len(row) == 1
    assert row[0].value == "ABC"
    assert row[0].location.sheet == "Sheet1"
    assert row[0].location.row == 1
    assert row[0].location.column == 1
    assert row[0].location.address == "A1"


def test_row_initialization_without_cells():
    """Test that a Row can be initialized without cells."""
    row = Row(index=2)
    assert row.index == 2
    assert len(row.cells) == 0