from aip_canonica.internal.models import Sheet, Workbook


def test_workbook():
    """Test that a Workbook can be initialized and a Sheet can be added."""
    workbook = Workbook()
    sheet = Sheet(name="Statement")
    workbook.sheets.append(sheet)
    assert len(workbook) == 1
    assert workbook.sheets[0] is sheet
    assert workbook.sheets[0].name == "Statement"