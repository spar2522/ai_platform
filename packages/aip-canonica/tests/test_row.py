from aip_canonica.internal.models import Cell, CellLocation, Row


def test_row():

    row = Row(index=1)

    row.cells.append(
        Cell(
            value="ABC",
            location=CellLocation(
                sheet="Sheet1",
                row=1,
                column=1,
                address="A1",
            ),
        )
    )

    assert len(row) == 1
    assert row[0].value == "ABC"
