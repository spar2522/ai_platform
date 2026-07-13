from aip_canonica.internal.models import CellLocation


def test_cell_location():
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