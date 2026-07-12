from dataclasses import dataclass

from .cell_location import CellLocation


@dataclass(slots=True)
class Cell:
    """
    Represents a single physical cell in a document.
    """

    value: object | None
    location: CellLocation
