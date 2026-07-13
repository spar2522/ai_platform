from aip_canonica.internal.models import Row, Sheet


def test_sheet():
    # Test that adding a row increases the sheet's length by 1
    sheet = Sheet(name="Statement")
    sheet.rows.append(Row(index=1))
    assert len(sheet) == 1


def test_sheet_multiple_rows():
    sheet = Sheet(name="Statement")
    sheet.rows.append(Row(index=1))
    sheet.rows.append(Row(index=2))
    assert len(sheet) == 2


def test_sheet_name():
    sheet = Sheet(name="Test Name")
    assert sheet.name == "Test Name"