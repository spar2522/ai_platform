from aip_canonica.internal.models import Cell, CellLocation


def test_cell():
    """Test the Cell model's initialization and properties."""
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