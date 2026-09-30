from aip_canonica.models import Cell, CellLocation


def test_cell_initialization():
    """Test the Cell model's initialization with valid parameters."""
    cell = Cell(
        value=100,
        location=CellLocation(
            sheet="Sheet1",
            row=1,
            column=1,
            address="A1",
        ),
    )

    assert cell.value == 100
    assert cell.location.sheet == "Sheet1"
    assert cell.location.row == 1
    assert cell.location.column == 1
    assert cell.location.address == "A1"


def test_cell_value_types():
    """Test the Cell model's ability to handle different value types."""
    # Test string value
    cell = Cell(value="test", location=CellLocation(sheet="Sheet1", row=1, column=1, address="A1"))
    assert cell.value == "test"

    # Test boolean value
    cell = Cell(value=True, location=CellLocation(sheet="Sheet1", row=1, column=1, address="A1"))
    assert cell.value is True

    # Test numeric value
    cell = Cell(value=3.14, location=CellLocation(sheet="Sheet1", row=1, column=1, address="A1"))
    assert cell.value == 3.14