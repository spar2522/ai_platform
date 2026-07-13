from aip_canonica import understand
from aip_canonica.internal.models import Workbook


def test_understand_returns_workbook(simple_workbook):
    workbook = understand(simple_workbook)

    assert isinstance(workbook, Workbook)
