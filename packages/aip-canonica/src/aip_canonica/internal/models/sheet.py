from dataclasses import dataclass, field

from .row import Row


@dataclass(slots=True)
class Sheet:
    """
    Represents one worksheet.
    """

    name: str

    rows: list[Row] = field(default_factory=list)

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index: int) -> Row:
        return self.rows[index]
