from aip_canonica.models import Row, Sheet


def test_sheet():
    """Test that adding a row to a sheet increases its length correctly."""
    sheet = Sheet(name="Statement")
    sheet.rows.append(Row(index=1))
    assert len(sheet) == 1