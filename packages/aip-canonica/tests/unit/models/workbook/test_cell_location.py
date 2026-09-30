from aip_canonica.models import CellLocation


def test_cell_location_initialization():
    """Test initialization of CellLocation with given parameters."""

    location = CellLocation(
        sheet="Statement",
        row=12,
        column=4,
        address="D12",
    )

    assert location.sheet == "Statement"
    assert location.row == 12
    assert location.column == 4
    assert location.address == "D12"


def test_cell_location_address_generation():
    """Test that address is generated correctly from row and column."""

    location = CellLocation(
        sheet="Statement",
        row=12,
        column=4,
    )

    assert location.address == "D12"


def test_cell_location_invalid_row():
    """Test that invalid row values are handled appropriately."""

    try:
        CellLocation(
            sheet="Statement",
            row=-5,
            column=4,
        )
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError for invalid row"


def test_cell_location_invalid_column():
    """Test that invalid column values are handled appropriately."""

    try:
        CellLocation(
            sheet="Statement",
            row=12,
            column=0,
        )
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError for invalid column"