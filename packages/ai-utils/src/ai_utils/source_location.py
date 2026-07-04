from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represents a location in a source document with multiple possible reference points.

    Attributes:
        page: Page number (for multi-page documents).
        sheet: Sheet name (for spreadsheet documents).
        row: Row number (for tabular data).
        column: Column identifier (for tabular data).
        line: Line number (for text-based documents).
    """
    page: Optional[int] = None
    sheet: Optional[str] = None
    row: Optional[int] = None
    column: Optional[str] = None
    line: Optional[int] = None