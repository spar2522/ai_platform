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
        return iter(self.cells)

    def __len__(self):
        return len(self.cells)

    def __getitem__(self, index: int) -> Cell:
        return self.cells[index]
