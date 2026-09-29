from aip_canonica.models import CellLocation


def test_cell_location():
    """Test initialization of CellLocation with given parameters and attribute assignments."""

    location = CellLocation(
        sheet="Statement",
        row=12,
        column=4,
        address="D12",
    )

    assert location.sheet == "Statement", "Sheet name should be correctly assigned"
    assert location.row == 12, "Row number should be correctly assigned"
    assert location.column == 4, "Column number should be correctly assigned"
    assert location.address == "D12", "Address should be correctly assigned"