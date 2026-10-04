from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from aip_canonica.models import (
    Cell,
    CellLocation,
    Row,
    Sheet,
    Workbook,
)
from .document_parser import DocumentParser


def _column_index_to_letter(col_idx: int) -> str:
    """Convert 1-based column integer index to Excel column letters (1 -> 'A', 27 -> 'AA')."""
    result = []
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))


class ExcelParser(DocumentParser):
    """Parses Excel spreadsheets, supporting modern .xlsx (OpenXML), legacy .xls (BIFF8 via xlrd),

    and HTML tables disguised as .xls files.
    """

    def parse(self, path: Path) -> Workbook:
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".xls":
            return self._parse_xls(path)

        try:
            return self._parse_xlsx(path)
        except Exception as exc:
            # If openpyxl failed because it was actually a legacy .xls or HTML file
            if "openpyxl does not support the old .xls" in str(exc) or suffix == ".xls":
                return self._parse_xls(path)
            raise

    def _parse_xlsx(self, path: Path) -> Workbook:
        workbook = Workbook()
        xl = load_workbook(filename=str(path), data_only=False)

        for worksheet in xl.worksheets:
            workbook.sheets.append(self._parse_sheet(worksheet))

        return workbook

    def _parse_sheet(self, worksheet: Any) -> Sheet:
        sheet = Sheet(name=worksheet.title)

        for row in worksheet.iter_rows():
            sheet.rows.append(self._parse_row(worksheet.title, row))

        return sheet

    def _parse_row(self, sheet_name: str, excel_row: Any) -> Row:
        row = Row(index=excel_row[0].row)

        for excel_cell in excel_row:
            row.cells.append(self._parse_cell(sheet_name, excel_cell))

        return row

    def _parse_cell(self, sheet_name: str, excel_cell: Any) -> Cell:
        return Cell(
            value=excel_cell.value,
            location=CellLocation(
                sheet=sheet_name,
                row=excel_cell.row,
                column=excel_cell.column,
                address=excel_cell.coordinate,
            ),
        )

    def _parse_xls(self, path: Path) -> Workbook:
        """Parse legacy .xls (BIFF8) or HTML tables saved with .xls extension."""
        try:
            return self._parse_biff8_xls(path)
        except Exception:
            if self._is_html_content(path):
                return self._parse_html_table(path)
            raise

    def _parse_biff8_xls(self, path: Path) -> Workbook:
        import xlrd

        rb = xlrd.open_workbook(filename=str(path))
        workbook = Workbook()

        for s_idx in range(rb.nsheets):
            sh = rb.sheet_by_index(s_idx)
            sheet = Sheet(name=sh.name)
            for r_idx in range(sh.nrows):
                row = Row(index=r_idx + 1)
                for c_idx in range(sh.ncols):
                    cell_val = sh.cell_value(r_idx, c_idx)
                    cell_type = sh.cell_type(r_idx, c_idx)
                    val_str = None

                    if cell_type == xlrd.XL_CELL_DATE:
                        try:
                            date_tuple = xlrd.xldate_as_tuple(cell_val, rb.datemode)
                            val_str = f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                        except Exception:
                            val_str = str(cell_val)
                    elif cell_type == xlrd.XL_CELL_NUMBER:
                        if cell_val == int(cell_val):
                            val_str = str(int(cell_val))
                        else:
                            val_str = str(cell_val)
                    elif cell_type == xlrd.XL_CELL_TEXT:
                        val_str = str(cell_val).strip() if cell_val is not None else None
                    elif cell_type == xlrd.XL_CELL_BOOLEAN:
                        val_str = str(bool(cell_val))
                    elif cell_type == xlrd.XL_CELL_EMPTY:
                        val_str = None
                    else:
                        val_str = str(cell_val) if cell_val else None

                    col_idx = c_idx + 1
                    cell = Cell(
                        value=val_str if val_str != "" else None,
                        location=CellLocation(
                            sheet=sh.name,
                            row=r_idx + 1,
                            column=col_idx,
                            address=f"{_column_index_to_letter(col_idx)}{r_idx + 1}",
                        ),
                    )
                    row.cells.append(cell)
                sheet.rows.append(row)
            workbook.sheets.append(sheet)

        return workbook

    def _is_html_content(self, path: Path) -> bool:
        try:
            with open(path, "rb") as f:
                head = f.read(512).lower()
            return b"<html" in head or b"<!doctype" in head or b"<table" in head
        except Exception:
            return False

    def _parse_html_table(self, path: Path) -> Workbook:
        from html.parser import HTMLParser

        class TableParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.rows: list[list[str]] = []
                self.current_row: list[str] = []
                self.current_cell: list[str] = []
                self.in_cell = False

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag in {"td", "th"}:
                    self.in_cell = True
                    self.current_cell = []
                elif tag == "tr":
                    self.current_row = []

            def handle_endtag(self, tag: str) -> None:
                if tag in {"td", "th"}:
                    self.in_cell = False
                    self.current_row.append("".join(self.current_cell).strip())
                elif tag == "tr":
                    if self.current_row:
                        self.rows.append(self.current_row)

            def handle_data(self, data: str) -> None:
                if self.in_cell:
                    self.current_cell.append(data)

        content = path.read_text(errors="ignore")
        parser = TableParser()
        parser.feed(content)

        workbook = Workbook()
        sheet = Sheet(name="Sheet1")
        for r_idx, row_vals in enumerate(parser.rows, start=1):
            row = Row(index=r_idx)
            for c_idx, val in enumerate(row_vals, start=1):
                cell = Cell(
                    value=val if val else None,
                    location=CellLocation(
                        sheet="Sheet1",
                        row=r_idx,
                        column=c_idx,
                        address=f"{_column_index_to_letter(c_idx)}{r_idx}",
                    ),
                )
                row.cells.append(cell)
            sheet.rows.append(row)
        workbook.sheets.append(sheet)
        return workbook
