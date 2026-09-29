from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell

from aip_canonica.models import (
    Workbook,
    Sheet,
    Row,
    Cell,
    CellLocation,
)

from .document_parser import DocumentParser


class ExcelParser(DocumentParser):
    """Parses Excel files into domain model objects representing workbooks, sheets, rows, and cells."""

    def parse(
        self,
        path: Path,
    ) -> Workbook:
        """Parse an Excel file located at the given path into a Workbook domain model object.

        Args:
            path: Path to the Excel file to parse.

        Returns:
            A Workbook object containing parsed sheets, rows, and cells.
        """
        workbook = Workbook()

        excel_workbook = load_workbook(
            filename=path,
            data_only=False,
        )

        for worksheet in excel_workbook.worksheets:
            workbook.sheets.append(self._parse_sheet(worksheet))

        return workbook

    def _parse_sheet(self, worksheet: Worksheet) -> Sheet:
        """Parse an Excel worksheet into a Sheet domain model object.

        Args:
            worksheet: The openpyxl Worksheet object to parse.

        Returns:
            A Sheet object containing parsed rows and cells.
        """
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
        """Parse an Excel row into a Row domain model object.

        Args:
            sheet_name: Name of the sheet containing the row.
            excel_row: A tuple of openpyxl Cell objects representing the row's cells.

        Returns:
            A Row object containing parsed cells and metadata.
        """
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
        excel_cell: Cell,
    ) -> Cell:
        """Parse an Excel cell into a Cell domain model object.

        Args:
            sheet_name: Name of the sheet containing the cell.
            excel_cell: An openpyxl Cell object representing the cell to parse.

        Returns:
            A Cell object containing the cell's value and location metadata.
        """
        return Cell(
            value=excel_cell.value,
            location=CellLocation(
                sheet=sheet_name,
                row=excel_cell.row,
                column=excel_cell.column,
                address=excel_cell.coordinate,
            ),
        )