import pytest

from aip_canonica import understand


def test_understand_not_implemented():
    """Verify that the understand function raises a NotImplementedError
    when called with a dummy file."""
    with pytest.raises(NotImplementedError):
        understand("dummy.xlsx")