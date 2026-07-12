from dataclasses import dataclass, field

from .sheet import Sheet


@dataclass(slots=True)
class Workbook:
    """
    Canonica's internal representation of a document.

    Every supported document format (Excel, CSV, PDF...)
    is first converted into a Workbook.
    """

    sheets: list[Sheet] = field(default_factory=list)

    def __iter__(self):
        return iter(self.sheets)

    def __len__(self):
        return len(self.sheets)

    def __getitem__(self, index: int) -> Sheet:
        return self.sheets[index]
