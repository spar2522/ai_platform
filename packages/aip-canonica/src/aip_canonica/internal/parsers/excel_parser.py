from pathlib import Path

from openpyxl import load_workbook

from aip_canonica.internal.models import (
    Workbook,
    Sheet,
    Row,
    Cell,
    CellLocation,
)

from .document_parser import DocumentParser


class ExcelParser(DocumentParser):

    def parse(
        self,
        path: Path,
    ) -> Workbook:

        workbook = Workbook()

        xl = load_workbook(
            filename=path,
            data_only=False,
        )

        for worksheet in xl.worksheets:

            workbook.sheets.append(self._parse_sheet(worksheet))

        return workbook

    def _parse_sheet(self, worksheet) -> Sheet:

        sheet = Sheet(
            name=worksheet.title,
        )

        for row in worksheet.iter_rows():

            sheet.rows.append(
                self._parse_row(
                    worksheet.title,
                    row,
                )
            )

        return sheet

    def _parse_row(
        self,
        sheet_name: str,
        excel_row,
    ) -> Row:

        row = Row(
            index=excel_row[0].row,
        )

        for excel_cell in excel_row:

            row.cells.append(
                self._parse_cell(
                    sheet_name,
                    excel_cell,
                )
            )

        return row

    def _parse_cell(
        self,
        sheet_name: str,
        excel_cell,
    ) -> Cell:

        return Cell(
            value=excel_cell.value,
            location=CellLocation(
                sheet=sheet_name,
                row=excel_cell.row,
                column=excel_cell.column,
                address=excel_cell.coordinate,
            ),
        )
