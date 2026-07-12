from aip_canonica.internal.models import Row, Sheet


def test_sheet():

    sheet = Sheet(name="Statement")

    sheet.rows.append(Row(index=1))

    assert len(sheet) == 1
