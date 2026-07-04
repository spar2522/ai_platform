from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represents a location in a document or data source.

    Attributes:
        page: Page number (for documents like PDFs).
        sheet: Sheet name (for spreadsheets like Excel).
        row: Row number (for tabular data).
        column: Column identifier (for tabular data, e.g., "A", "B").
        line: Line number (for text files or code).
    """

    page: int | None = None
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    line: int | None = None