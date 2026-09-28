from dataclasses import dataclass, field

from .row import Row


@dataclass(slots=True)
class Sheet:
    """
    Represents one worksheet.

    A sheet contains a name and a collection of rows. The name must be a non-empty string, and rows are a list of Row objects.
    """

    name: str
    rows: list[Row] = field(default_factory=list)

    def __iter__(self):
        """
        Iterate over the rows in the sheet.
        """
        return iter(self.rows)

    def __len__(self):
        """
        Return the number of rows in the sheet.
        """
        return len(self.rows)

    def __getitem__(self, index: int) -> Row:
        """
        Access the row at the specified index.

        Raises:
            IndexError: If the index is out of range.
        """
        return self.rows[index]