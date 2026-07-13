from aip_canonica import understand
from aip_canonica.internal.models import Workbook


def test_understand_returns_workbook(simple_workbook):
    workbook = understand(simple_workbook)

    assert isinstance(workbook, Workbook)


def test_understand_not_implemented():
    """Verify that the understand function raises a NotImplementedError
    when called with a dummy file."""
    with pytest.raises(NotImplementedError):
        understand("dummy.xlsx")