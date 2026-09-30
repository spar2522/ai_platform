"""Extractor protocol defining the interface for layout-specific conversion."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aip_canonica.models.base import CanonicalDocument
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models import Workbook


@runtime_checkable
class Extractor(Protocol):
    """Protocol for converting raw physical workbook representations into canonical models.

    This interface defines the standard operations required for all extractors. Implementations
    must provide concrete logic for matching workbooks and performing the canonical conversion.
    """

    @property
    def document_type(self) -> DocumentType:
        """The canonical document type produced by this extractor.

        This property identifies the type of canonical document this extractor is responsible for.
        """
        ...

    @property
    def name(self) -> str:
        """Name of the extractor / document family strategy.

        This provides a human-readable identifier for the extractor, useful for debugging and
        logging purposes.
        """
        ...

    @property
    def is_generic(self) -> bool:
        """Whether this is a generic fallback extractor (True) or layout-specialized (False).

        Generic extractors are used when no more specific extractor matches the workbook's structure.
        """
        ...

    def matches(self, workbook: Workbook) -> bool:
        """Determine applicability BEFORE extraction based on structural anchors.

        This method should analyze the workbook's structure to determine if this extractor can
        handle it. It should not perform any actual extraction, only validation.
        """
        ...

    def extract(self, workbook: Workbook, *, source_name: str = "") -> CanonicalDocument:
        """Deterministically convert the workbook into a canonical financial object.

        This is the core method responsible for transforming the workbook into a standardized
        canonical document. The source_name parameter is optional and may be used for tracking
        the origin of the data if needed.

        Args:
            workbook: The physical workbook representation to be converted.
            source_name: Optional identifier for the source of the workbook data.

        Returns:
            A canonical document model representing the converted workbook.
        """
        ...