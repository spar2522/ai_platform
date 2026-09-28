"""Extractor protocol defining the interface for layout-specific conversion."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aip_canonica.models.base import CanonicalDocument
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models import Workbook


@runtime_checkable
class Extractor(Protocol):
    """Protocol for converting raw physical workbook representations into canonical models."""

    @property
    def document_type(self) -> DocumentType:
        """The canonical document type produced by this extractor."""
        ...

    @property
    def name(self) -> str:
        """Name of the extractor / document family strategy."""
        ...

    @property
    def is_generic(self) -> bool:
        """Whether this is a generic fallback extractor (True) or layout-specialized (False)."""
        ...

    def matches(self, workbook: Workbook) -> bool:
        """Determine applicability BEFORE extraction based on structural anchors."""
        ...

    def extract(self, workbook: Workbook, *, source_name: str = "") -> CanonicalDocument:
        """Deterministically convert the workbook into a canonical financial object."""
        ...
