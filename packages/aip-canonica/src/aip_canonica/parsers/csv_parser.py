"""CSV document parser converting CSV files into Workbook models."""

from __future__ import annotations

import csv
from pathlib import Path

from aip_canonica.models import Cell, CellLocation, Row, Sheet, Workbook
from aip_canonica.parsers.document_parser import DocumentParser


def _column_index_to_letter(col_idx: int) -> str:
    """Convert 1-based column index to Excel-style column letter (1 -> 'A', 27 -> 'AA')."""
    letters = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


class CsvParser(DocumentParser):
    """Parses delimited CSV files into Canonica's Workbook representation."""

    def parse(self, path: Path) -> Workbook:
        path = Path(path)
        sheet_name = path.stem or "Sheet1"

        # Try reading with utf-8-sig (handles BOM), fall back to latin-1
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()

        sheet = Sheet(name=sheet_name)
        lines = content.splitlines()

        # If empty document
        if not lines:
            workbook = Workbook()
            workbook.sheets.append(sheet)
            return workbook

        # Detect delimiter if possible, default to comma
        sample = "\n".join(lines[:10])
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.reader(lines, delimiter=delimiter)

        for row_idx, row_values in enumerate(reader, start=1):
            row = Row(index=row_idx)
            for col_idx, val in enumerate(row_values, start=1):
                # Clean stripped value or None
                clean_val = val.strip() if val is not None else None
                cell = Cell(
                    value=clean_val,
                    location=CellLocation(
                        sheet=sheet_name,
                        row=row_idx,
                        column=col_idx,
                        address=f"{_column_index_to_letter(col_idx)}{row_idx}",
                    ),
                )
                row.cells.append(cell)
            sheet.rows.append(row)

        workbook = Workbook()
        workbook.sheets.append(sheet)
        return workbook
