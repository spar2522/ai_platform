from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represents the location of a piece of data within a source document.

    Attributes:
        page: The page number in a multi-page document (e.g., PDF).
        sheet: The name of the sheet in a spreadsheet document (e.g., Excel).
        row: The row number in a tabular structure.
        column: The column identifier in a tabular structure (e.g., "A", "B2").
        line: The line number in a text-based document.
    """

    page: int | None = None
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    line: int | None = None