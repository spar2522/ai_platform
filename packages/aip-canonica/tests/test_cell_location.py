from aip_canonica.internal.models import CellLocation


def test_cell_location():

    location = CellLocation(
        sheet="Statement",
        row=12,
        column=4,
        address="D12",
    )

    assert location.sheet == "Statement"
    assert location.address == "D12"
