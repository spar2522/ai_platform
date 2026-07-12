from aip_canonica.internal.models import Sheet, Workbook


def test_workbook():

    workbook = Workbook()

    workbook.sheets.append(Sheet(name="Statement"))

    assert len(workbook) == 1
