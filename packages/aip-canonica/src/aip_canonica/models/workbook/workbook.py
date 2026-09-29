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

    Methods:
        __iter__: Iterates over the sheets.
        __len__: Returns the number of sheets.
        __getitem__: Accesses a sheet by index.
    """

    sheets: list[Sheet] = field(default_factory=list)

    def __post_init__(self):
        for sheet in self.sheets:
            if not isinstance(sheet, Sheet):
                raise TypeError(f"Each sheet must be an instance of Sheet, got {type(sheet)}")

    def __iter__(self):
        return iter(self.sheets)

    def __len__(self):
        return len(self.sheets)

    def __getitem__(self, index: int) -> Sheet:
        return self.sheets[index]

    def __repr__(self):
        return f"Workbook(sheets={len(self.sheets)} sheets)"