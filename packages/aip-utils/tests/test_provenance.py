from aip_utils.provenance import Provenance


def test_import():
    """Test that the Provenance class can be imported without errors."""
    assert Provenance is not None