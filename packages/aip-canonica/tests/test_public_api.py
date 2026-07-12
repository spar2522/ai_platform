import pytest

from aip_canonica import understand


def test_understand_not_implemented():
    with pytest.raises(NotImplementedError):
        understand("dummy.xlsx")
