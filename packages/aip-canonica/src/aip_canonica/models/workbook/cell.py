from dataclasses import dataclass

from .cell_location import CellLocation


@dataclass(slots=True)
class Cell:
    """
    Represents a single physical cell in a document.

    Attributes:
        value: The content of the cell. Can be None if the cell is empty.
        location: The location of the cell within the document.
    """

    value: object | None
    location: CellLocation