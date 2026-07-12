from aip_canonica.internal.models import Row, Sheet


def test_sheet():
    """Test the Sheet and Row models."""
    # Create a sheet with a specific name
    sheet = Sheet(name="Statement")
    # Verify the sheet's name is set correctly
    assert sheet.name == "Statement"

    # Create a row with a specific index
    row = Row(index=1)
    # Add the row to the sheet
    sheet.rows.append(row)

    # Verify the row was added correctly
    assert len(sheet) == 1
    assert sheet.rows[0] == row
    assert sheet.rows[0].index == 1