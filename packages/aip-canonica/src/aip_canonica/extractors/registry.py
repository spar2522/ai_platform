"""Registry for discovering and selecting matching extractors."""

from __future__ import annotations

from typing import Any, Sequence

from aip_canonica.extractors.bank.icici import ICICIBankStatementExtractor
from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.invoice.tabular import TabularInvoiceExtractor
from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor
from aip_canonica.models import Workbook


class ExtractorRegistry:
    """Registry maintaining known layout-specific extractors."""

    def __init__(self, extractors: Sequence[Extractor] | None = None) -> None:
        self._extractors: list[Extractor] = list(extractors or [])

    def register(self, extractor: Extractor) -> None:
        """Register a new extraction strategy."""
        self._extractors.append(extractor)

    def find_specialized_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find the first matching specialized (non-generic) extractor.

        Returns:
            Extractor: First matching specialized extractor, or None if none match.
        """
        for extractor in self._extractors:
            if not getattr(extractor, "is_generic", False) and extractor.matches(workbook):
                return extractor
        return None

    def find_generic_extractor(
        self, workbook: Workbook, *, document_type: Any | None = None
    ) -> Extractor | None:
        """Find the first matching generic fallback extractor, optionally matching document_type.

        Args:
            document_type: Optional document type to filter extractors.

        Returns:
            Extractor: First matching generic extractor, or None if none match.
        """
        for extractor in self._extractors:
            if getattr(extractor, "is_generic", False):
                extractor_document_type = getattr(extractor, "document_type", None)
                if document_type is None or extractor_document_type == document_type:
                    if extractor.matches(workbook):
                        return extractor
        return None

    def find_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find matching extractor, prioritizing specialized over generic fallback.

        Returns:
            Extractor: First matching extractor, or None if none match.
        """
        specialized = self.find_specialized_extractor(workbook)
        if specialized is not None:
            return specialized
        return self.find_generic_extractor(workbook)

    def get_extractors(self) -> list[Extractor]:
        """Return all registered extractors.

        Returns:
            list[Extractor]: A list of all registered extractors.
        """
        return list(self._extractors)

    def clear(self) -> None:
        """Clear all registered extractors."""
        self._extractors.clear()


_DEFAULT_REGISTRY: ExtractorRegistry | None = None


def get_default_registry() -> ExtractorRegistry:
    """Return the global default ExtractorRegistry populated with built-in extractors."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ExtractorRegistry(
            [
                ICICIBankStatementExtractor(),
                StandardBankStatementExtractor(),
                TabularInvoiceExtractor(),
                TabularLedgerExtractor(),
            ]
        )
    return _DEFAULT_REGISTRY


def register_extractor(extractor: Extractor) -> None:
    """Register an extractor into the global default registry."""
    get_default_registry().register(extractor)