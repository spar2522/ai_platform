from aip_canonica.internal.models import Cell, CellLocation


def test_cell():

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
    assert cell.location.address == "A1"
