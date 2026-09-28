from dataclasses import dataclass, field

from .cell import Cell


@dataclass(slots=True)
class Row:
    """
    Represents one physical row in a sheet.
    """

    index: int

    cells: list[Cell] = field(default_factory=list)

    def __iter__(self):
        """Return an iterator over the cells in the row."""
        return iter(self.cells)

    def __len__(self):
        """Return the number of cells in the row."""
        return len(self.cells)

    def __getitem__(self, index: int) -> Cell:
        """Return the cell at the specified index."""
        return self.cells[index]

    def __repr__(self):
        """Return a string representation of the Row instance."""
        return f"Row(index={self.index}, cells={len(self.cells)} cells)"