"""Physical location of a cell in a tabular structure."""

import re
from typing import Any, Dict

def column_to_letter(column: int) -> str:
    """Convert a column number to a letter (e.g., 1 -> 'A', 27 -> 'AA')."""
    letters = ''
    while column > 0:
        column, remainder = divmod(column - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters

class CellReference:
    """Represents a reference to a cell in a tabular structure with row and column indices.
    
    Attributes:
        sheet: Name of the sheet containing the cell.
        row: Row number of the cell (1-based).
        column: Column number of the cell (1-based).
        address: Cell reference in the format "A1", "B2", etc.
    """
    
    def __init__(self, sheet: str, row: int, column: int, address: str):
        self.sheet = sheet
        self.row = row
        self.column = column
        self.address = address

    def __post_init__(self):
        """Validate that the address matches the row and column."""
        expected_address = f"{column_to_letter(self.column)}{self.row}"
        if self.address != expected_address:
            raise ValueError(f"Address must be '{expected_address}', but got '{self.address}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the cell reference to a dictionary."""
        return {
            "sheet": self.sheet,
            "row": self.row,
            "column": self.column,
            "address": self.address,
        }

    def __repr__(self) -> str:
        return f"CellReference(sheet='{self.sheet}', row={self.row}, column={self.column}, address='{self.address}')"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CellReference):
            return False
        return (self.sheet == other.sheet and
                self.row == other.row and
                self.column == other.column and
                self.address == other.address)

    def __hash__(self) -> int:
        return hash((self.sheet, self.row, self.column, self.address))