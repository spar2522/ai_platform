"""First-class provenance tracking for extracted financial entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from aip_canonica.models.workbook.cell_location import CellLocation
from aip_utils.provenance import Provenance as AIPUtilsProvenance
from aip_utils.source_location import SourceLocation

__all__ = ["Provenance"]


@dataclass(frozen=True, slots=True)
class Provenance:
    """Describes where an extracted object or field originated.

    Attributes:
        source: The source identifier (e.g., file path or database ID).
        sheet: The name of the sheet (for spreadsheets).
        row: The row number (for spreadsheets or CSV files).
        column: The column number or name (for spreadsheets or CSV files).
        address: A human-readable cell address (e.g., "A1", "Sheet1!B2").
        page: The page number (for PDFs or scanned documents).
        line: The line number (for CSV files).
        cells: A tuple of `CellLocation` objects representing specific cells.
        metadata: Additional metadata associated with the provenance.
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
        """Create a Provenance instance from a single `CellLocation`.

        Args:
            location: The cell location.
            source: The source identifier (optional).
            metadata: Additional metadata (optional).
        """
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
        """Create a Provenance instance from multiple `CellLocation` objects.

        Args:
            cells: A sequence of cell locations.
            source: The source identifier (optional).
            sheet: Override the sheet name from the first cell (optional).
            row: Override the row number from the first cell (optional).
            metadata: Additional metadata (optional).
        """
        first = cells[0] if cells else None
        return cls(
            source=source,
            sheet=sheet or (first.sheet if first else None),
            row=row or (first.row if first else None),
            column=first.column if first else None,
            address=first.address if first else None,
            page=first.page if first else None,
            line=first.line if first else None,
            cells=tuple(cells),
            metadata=metadata or {},
        )

    @classmethod
    def from_cell_address(
        cls,
        address: str,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Provenance:
        """Create a Provenance instance from a cell address string.

        Args:
            address: A string representing the cell address (e.g., "A1", "Sheet1!B2").
            source: The source identifier (optional).
            metadata: Additional metadata (optional).
        """
        # Simplified example; actual implementation may require parsing the address
        return cls(
            source=source,
            address=address,
            metadata=metadata or {},
        )

    def to_utils_provenance(self) -> AIPUtilsProvenance:
        """Convert to `AIPUtilsProvenance` object for compatibility."""
        return AIPUtilsProvenance(
            source=self.source,
            sheet=self.sheet,
            row=self.row,
            column=str(self.column) if self.column is not None else None,
            page=self.page,
            line=self.line,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the Provenance instance to a dictionary."""
        data = {
            "source": self.source,
            "sheet": self.sheet,
            "row": self.row,
            "column": self.column,
            "address": self.address,
            "page": self.page,
            "line": self.line,
            "metadata": self.metadata,
        }
        if self.cells:
            data["cells"] = [cell.to_dict() for cell in self.cells]
        return {k: v for k, v in data.items() if v is not None}