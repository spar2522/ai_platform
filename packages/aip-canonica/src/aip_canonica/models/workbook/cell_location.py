"""Physical location of a cell in a tabular document."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aip_utils.source_location import SourceLocation


@dataclass(frozen=True, slots=True)
class CellLocation:
    """Physical location of a cell in the original document.

    Attributes:
        sheet: Name of the sheet containing the cell.
        row: 1-based row number of the cell.
        column: 1-based column number of the cell.
        address: String representation of the cell's address (e.g., "A1").

    Example:
        >>> CellLocation(sheet="Sheet1", row=1, column=1, address="A1")
        CellLocation(sheet='Sheet1', row=1, column=1, address='A1')
    """

    sheet: str
    row: int
    column: int
    address: str

    def to_source_location(self) -> SourceLocation:
        """Convert to standard aip_utils SourceLocation."""
        return SourceLocation(
            sheet=self.sheet,
            row=self.row,
            column=str(self.column),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "sheet": self.sheet,
            "row": self.row,
            "column": self.column,
            "address": self.address,
        }

    def __repr__(self) -> str:
        return f"CellLocation(sheet={self.sheet!r}, row={self.row}, column={self.column}, address={self.address!r})"