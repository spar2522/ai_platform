"""Unit tests for CellLocation and Provenance."""

from aip_canonica.models.provenance import CellLocation, Provenance
from aip_utils.provenance import Provenance as AIPUtilsProvenance


def test_cell_location_properties():
    loc = CellLocation(sheet="Sheet1", row=10, column=2, address="B10")
    assert loc.sheet == "Sheet1"
    assert loc.row == 10
    assert loc.column == 2
    assert loc.address == "B10"

    src_loc = loc.to_source_location()
    assert src_loc.sheet == "Sheet1"
    assert src_loc.row == 10
    assert src_loc.column == "2"

    d = loc.to_dict()
    assert d == {"sheet": "Sheet1", "row": 10, "column": 2, "address": "B10"}


def test_provenance_from_cell_location():
    loc = CellLocation(sheet="Sheet1", row=5, column=3, address="C5")
    prov = Provenance.from_cell_location(loc, source="test.xlsx", metadata={"rule": "anchor"})

    assert prov.source == "test.xlsx"
    assert prov.sheet == "Sheet1"
    assert prov.row == 5
    assert prov.column == 3
    assert prov.address == "C5"
    assert len(prov.cells) == 1
    assert prov.cells[0] == loc
    assert prov.metadata["rule"] == "anchor"

    utils_prov = prov.to_utils_provenance()
    assert isinstance(utils_prov, AIPUtilsProvenance)
    assert utils_prov.source == "test.xlsx"
    assert utils_prov.location is not None
    assert utils_prov.location.sheet == "Sheet1"


def test_provenance_from_cells():
    cells = [
        CellLocation(sheet="Sheet1", row=2, column=1, address="A2"),
        CellLocation(sheet="Sheet1", row=2, column=2, address="B2"),
    ]
    prov = Provenance.from_cells(cells, source="test.xlsx")
    assert prov.sheet == "Sheet1"
    assert prov.row == 2
    assert len(prov.cells) == 2


def test_provenance_from_line_and_page():
    line_prov = Provenance.from_line(42, source="file.csv")
    assert line_prov.line == 42
    assert line_prov.source == "file.csv"

    page_prov = Provenance.from_page(3, source="doc.pdf")
    assert page_prov.page == 3
    assert page_prov.source == "doc.pdf"


def test_provenance_serialization():
    prov = Provenance(source="source.xlsx", sheet="Sheet0", row=15, address="A15")
    d = prov.to_dict()
    assert d["source"] == "source.xlsx"
    assert d["sheet"] == "Sheet0"
    assert d["row"] == 15
    assert d["address"] == "A15"