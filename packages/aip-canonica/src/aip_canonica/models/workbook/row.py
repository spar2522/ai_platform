from dataclasses import dataclass, field

from .cell import Cell


@dataclass(slots=True)
class Row:
    """
    Represents one physical row in a sheet. Used to store and access individual cells
    within a row during workbook parsing and validation.
    """

    index: int
    cells: list[Cell] = field(default_factory=list)

    def __iter__(self):
        """Return an iterator over the cells in the row, allowing for sequential access."""
        return iter(self.cells)

    def __len__(self):
        """Return the number of cells in the row, useful for determining row size."""
        return len(self.cells)

    def __getitem__(self, index: int) -> Cell:
        """Return the cell at the specified index, similar to list indexing."""
        return self.cells[index]

    def __repr__(self):
        """Return a string representation of the Row instance, useful for debugging."""
        return f"Row(index={self.index}, cells={len(self)} cells)"