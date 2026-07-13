from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CellLocation:
    """
    Physical location of a cell in the original document.

    Attributes:
        sheet: Name of the sheet containing the cell.
        row: 1-based row number of the cell.
        column: 1-based column number of the cell.
        address: String representation of the cell's address (e.g., "A1").
    """

    sheet: str
    row: int
    column: int
    address: str