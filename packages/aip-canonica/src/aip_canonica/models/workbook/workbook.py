from dataclasses import dataclass, field

from .sheet import Sheet


@dataclass(slots=True)
class Workbook:
    """
    Canonica's internal representation of a document.

    Every supported document format (Excel, CSV, PDF...)
    is first converted into a Workbook. The Workbook serves as a
    container for one or more Sheet objects, which represent
    individual pages or worksheets within the document.

    Attributes:
        sheets: A list of Sheet objects that make up the document.
    """

    sheets: list[Sheet] = field(default_factory=list)

    def __iter__(self):
        """Iterate over the sheets in the workbook."""
        return iter(self.sheets)

    def __len__(self):
        """Return the number of sheets in the workbook."""
        return len(self.sheets)

    def __getitem__(self, index: int) -> Sheet:
        """Access a sheet by its index.

        Args:
            index: The index of the sheet to retrieve.

        Returns:
            The Sheet at the specified index.
        """
        return self.sheets[index]