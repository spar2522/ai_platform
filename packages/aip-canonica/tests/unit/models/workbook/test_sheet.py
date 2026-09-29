from aip_canonica.models import Row, Sheet


def test_sheet():
    """Test basic Sheet initialization and row appending."""
    sheet = Sheet(name="Statement")
    assert sheet.name == "Statement"
    sheet.rows.append(Row(index=1))
    assert len(sheet) == 1
    assert sheet.rows[0].index == 1


def test_empty_sheet():
    """Test Sheet with no rows."""
    sheet = Sheet(name="Empty")
    assert len(sheet) == 0


def test_adding_multiple_rows():
    """Test adding multiple rows to a Sheet."""
    sheet = Sheet(name="Multiple")
    sheet.rows.append(Row(index=1))
    sheet.rows.append(Row(index=2))
    assert len(sheet) == 2
    assert sheet.rows[0].index == 1
    assert sheet.rows[1].index == 2