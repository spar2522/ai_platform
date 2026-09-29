"""Unit tests for CellLocation and Provenance."""

from aip_canonica.models.provenance import CellLocation, Provenance
from aip_utils.provenance import Provenance as AIPUtilsProvenance


def test_cell_location_properties():
    cell_location = CellLocation(sheet="Sheet1", row=10, column=2, address="B10")
    assert cell_location.sheet == "Sheet1"
    assert cell_location.row == 10
    assert cell_location.column == 2
    assert cell_location.address == "B10"

    source_location = cell_location.to_source_location()
    assert source_location.sheet == "Sheet1"
    assert source_location.row == 10
    assert source_location.column == "2"

    dict_representation = cell_location.to_dict()
    assert dict_representation == {"sheet": "Sheet1", "row": 10, "column": 2, "address": "B10"}


def test_provenance_from_cell_location():
    cell_location = CellLocation(sheet="Sheet1", row=5, column=3, address="C5")
    provenance = Provenance.from_cell_location(
        cell_location, source="test.xlsx", metadata={"rule": "anchor"}
    )

    assert provenance.source == "test.xlsx"
    assert provenance.sheet == "Sheet1"
    assert provenance.row == 5
    assert provenance.column == 3
    assert provenance.address == "C5"
    assert len(provenance.cells) == 1
    assert provenance.cells[0] == cell_location
    assert provenance.metadata["rule"] == "anchor"

    utils_provenance = provenance.to_utils_provenance()
    assert isinstance(utils_provenance, AIPUtilsProvenance)
    assert utils_provenance.source == "test.xlsx"
    assert utils_provenance.location is not None
    assert utils_provenance.location.sheet == "Sheet1"


def test_provenance_from_cells():
    cells = [
        CellLocation(sheet="Sheet1", row=2, column=1, address="A2"),
        CellLocation(sheet="Sheet1", row=2, column=2, address="B2"),
    ]
    provenance = Provenance.from_cells(cells, source="test.xlsx")
    assert provenance.sheet == "Sheet1"
    assert provenance.row == 2
    assert len(provenance.cells) == 2


def test_provenance_from_line_and_page():
    line_provenance = Provenance.from_line(42, source="file.csv")
    assert line_provenance.line == 42
    assert line_provenance.source == "file.csv"

    page_provenance = Provenance.from_page(3, source="doc.pdf")
    assert page_provenance.page == 3
    assert page_provenance.source == "doc.pdf"


def test_provenance_serialization():
    provenance = Provenance(source="source.xlsx", sheet="Sheet0", row=15, address="A15")
    dict_representation = provenance.to_dict()
    assert dict_representation["source"] == "source.xlsx"
    assert dict_representation["sheet"] == "Sheet0"
    assert dict_representation["row"] == 15
    assert dict_representation["address"] == "A15"