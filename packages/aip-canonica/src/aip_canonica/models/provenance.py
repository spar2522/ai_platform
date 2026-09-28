"""First-class provenance tracking for extracted financial entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from aip_canonica.models.workbook.cell_location import CellLocation
from aip_utils.provenance import Provenance as AIPUtilsProvenance
from aip_utils.source_location import SourceLocation

__all__ = ["CellLocation", "Provenance"]


@dataclass(frozen=True, slots=True)
class Provenance:
    """Describes where an extracted object or field originated.

    Supports spreadsheets (cells, rows, sheets), CSV (lines),
    PDF/OCR (pages, regions), and future physical formats.
    """

    source: str
    sheet: str | None = None
    row: int | None = None
    column: int | str | None = None
    address: str | None = None
    page: int | None = None
    line: int | None = None
    cells: tuple[CellLocation, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cell_location(
        cls,
        location: CellLocation,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Provenance:
        return cls(
            source=source,
            sheet=location.sheet,
            row=location.row,
            column=location.column,
            address=location.address,
            cells=(location,),
            metadata=metadata or {},
        )

    @classmethod
    def from_cells(
        cls,
        cells: Sequence[CellLocation],
        source: str = "",
        sheet: str | None = None,
        row: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Provenance:
        first = cells[0] if cells else None
        return cls(
            source=source,
            sheet=sheet or (first.sheet if first else None),
            row=row or (first.row if first else None),
            cells=tuple(cells),
            metadata=metadata or {},
        )

    @classmethod
    def from_line(
        cls,
        line: int,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Provenance:
        return cls(
            source=source,
            line=line,
            metadata=metadata or {},
        )

    @classmethod
    def from_page(
        cls,
        page: int,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Provenance:
        return cls(
            source=source,
            page=page,
            metadata=metadata or {},
        )

    def to_utils_provenance(self) -> AIPUtilsProvenance:
        """Convert to platform-level aip_utils.Provenance."""
        return AIPUtilsProvenance(
            source=self.source,
            location=SourceLocation(
                page=self.page,
                sheet=self.sheet,
                row=self.row,
                column=str(self.column) if self.column is not None else None,
                line=self.line,
            ),
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"source": self.source}
        if self.sheet is not None:
            data["sheet"] = self.sheet
        if self.row is not None:
            data["row"] = self.row
        if self.column is not None:
            data["column"] = self.column
        if self.address is not None:
            data["address"] = self.address
        if self.page is not None:
            data["page"] = self.page
        if self.line is not None:
            data["line"] = self.line
        if self.cells:
            data["cells"] = [c.to_dict() for c in self.cells]
        if self.metadata:
            data["metadata"] = self.metadata
        return data
