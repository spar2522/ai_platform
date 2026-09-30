from pathlib import Path

from openpyxl import load_workbook

from aip_canonica.models import (
    Workbook,
    Sheet,
    Row,
    Cell,
    CellLocation,
)

from .document_parser import DocumentParser


class ExcelParser(DocumentParser):
    """Parses Excel files into domain model objects (Workbook, Sheet, Row, Cell)."""

    def parse(
        self,
        path: Path,
    ) -> Workbook:
        """
        Parse an Excel file into a Workbook domain model object.

        Args:
            path: Path to the Excel file to parse.

        Returns:
            A Workbook object containing all parsed sheets, rows, and cells.
        """
        workbook = Workbook()

        xl = load_workbook(
            filename=path,
            data_only=False,
        )

        for worksheet in xl.worksheets:
            workbook.sheets.append(self._parse_sheet(worksheet))

        return workbook

    def _parse_sheet(self, worksheet) -> Sheet:
        """
        Convert an openpyxl Worksheet into a domain model Sheet object.

        Args:
            worksheet: The openpyxl Worksheet object to parse.

        Returns:
            A Sheet object containing all parsed rows from the worksheet.
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
        """
        Convert an openpyxl row into a domain model Row object.

        Args:
            sheet_name: Name of the sheet containing the row.
            excel_row: Iterable of openpyxl Cell objects representing the row.

        Returns:
            A Row object containing all parsed cells from the row.
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
        excel_cell,
    ) -> Cell:
        """
        Convert an openpyxl Cell into a domain model Cell object.

        Args:
            sheet_name: Name of the sheet containing the cell.
            excel_cell: openpyxl Cell object to parse.

        Returns:
            A Cell object containing the value and location of the cell.
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