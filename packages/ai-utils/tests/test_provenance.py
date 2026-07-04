from ai_utils.provenance import Provenance


def test_import():
    """Verify that the Provenance class can be imported and is a valid class."""
    assert Provenance is not None
    assert isinstance(Provenance, type)