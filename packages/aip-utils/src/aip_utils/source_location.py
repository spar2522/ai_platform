from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    page: int | None = None
    source_url: str | None = None
    row: int | None = None
    column: str | None = None
    line: int | None = None
