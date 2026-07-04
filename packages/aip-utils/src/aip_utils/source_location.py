from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represents the location of a source in a document or data structure."""
    page: int | None = None
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    line: int | None = None