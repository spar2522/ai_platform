from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represents the location of a source in a document or file.

    Attributes:
        page: Page number in a multi-page document (e.g., PDF, book).
        source_url: URL where the source data is located (e.g., web page, API endpoint).
        row: Row number in a spreadsheet or table.
        column: Column identifier in a spreadsheet or table (e.g., "A", "B", "C").
        line: Line number in a text file or code file.
    """
    page: int | None = None
    source_url: str | None = None
    row: int | None = None
    column: str | None = None
    line: int | None = None