"""Extractor protocol defining the interface for layout-specific conversion."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aip_canonica.models.base import CanonicalDocument
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models import Workbook


@runtime_checkable
class Extractor(Protocol):
    """Protocol for converting raw physical workbook representations into canonical models.

    Implementations must define methods to validate workbook structure and perform
    deterministic conversion to canonical financial objects. This interface enables
    polymorphic handling of different document layouts and formats.
    """

    @property
    def document_type(self) -> DocumentType:
        """The canonical document type produced by this extractor.

        This defines the semantic category of the output (e.g., invoice, receipt,
        financial statement) after successful extraction.
        """
        ...

    @property
    def name(self) -> str:
        """Name of the extractor / document family strategy.

        Used for identification and logging purposes. Should be unique within
        a given document type category.
        """
        ...

    @property
    def is_generic(self) -> bool:
        """Whether this is a generic fallback extractor (True) or layout-specialized (False).

        Generic extractors are used when no more specific matcher is available.
        """
        ...

    def matches(self, workbook: Workbook) -> bool:
        """Determine applicability BEFORE extraction based on structural anchors.

        This method should perform lightweight validation of workbook structure
        without modifying the workbook content. Returns True if the extractor can
        handle the workbook's layout.
        """
        ...

    def extract(self, workbook: Workbook, *, source_name: str = "") -> CanonicalDocument:
        """Deterministically convert the workbook into a canonical financial object.

        Args:
            workbook: The physical workbook representation to convert
            source_name: Optional identifier for the original source (e.g., file path,
                system name) - used for provenance tracking

        Returns:
            A fully validated canonical document object
        """
        ...