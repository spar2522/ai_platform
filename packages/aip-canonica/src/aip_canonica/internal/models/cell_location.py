from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CellLocation:
    """
    Physical location of a cell in the original document.
    """

    sheet: str
    row: int
    column: int
    address: str
