"""Registry for discovering and selecting matching extractors."""

from __future__ import annotations

from typing import Any, Sequence

from aip_canonica.extractors.bank.icici import ICICIBankStatementExtractor
from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.invoice.tabular import TabularInvoiceExtractor
from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor
from aip_canonica.extractors.bank.axis_bank import AxisBankStatementExtractor
from aip_canonica.models import Workbook


class ExtractorRegistry:
    """Registry maintaining known layout-specific extractors.

    This class provides methods to register extractors and find the best match
    for a given workbook, prioritizing specialized extractors over generic ones.
    """

    def __init__(self, extractors: Sequence[Extractor] | None = None) -> None:
        """Initialize the registry with an optional list of extractors.

        Args:
            extractors: A sequence of Extractor instances to register.
                Defaults to an empty list if not provided.
        """
        self._extractors: list[Extractor] = list(extractors or [])

    def register(self, extractor: Extractor) -> None:
        """Register a new extraction strategy.

        Args:
            extractor: The Extractor instance to register.
        """
        self._extractors.append(extractor)

    def find_specialized_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find the first matching specialized (non-generic) extractor.

        Specialized extractors are those that are not marked as generic
        (i.e., do not have the 'is_generic' attribute or it is set to False).

        Args:
            workbook: The workbook to match against.

        Returns:
            The first matching specialized extractor, or None if none match.
        """
        for extractor in self._extractors:
            if not getattr(extractor, "is_generic", False) and extractor.matches(workbook):
                return extractor
        return None

    def find_generic_extractor(
        self, workbook: Workbook, *, document_type: Any | None = None
    ) -> Extractor | None:
        """Find the first matching generic fallback extractor.

        Generic extractors are marked with the 'is_generic' attribute.
        This method optionally filters by document_type if provided.

        Args:
            workbook: The workbook to match against.
            document_type: Optional document type to filter extractors by.

        Returns:
            The first matching generic extractor, or None if none match.
        """
        for extractor in self._extractors:
            if getattr(extractor, "is_generic", False):
                if document_type is None or extractor.document_type == document_type:
                    if extractor.matches(workbook):
                        return extractor
        return None

    def find_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find matching extractor, prioritizing specialized over generic fallback.

        This method first checks for specialized extractors and falls back to
        generic extractors if none are found.

        Args:
            workbook: The workbook to match against.

        Returns:
            The first matching extractor, or None if none match.
        """
        specialized = self.find_specialized_extractor(workbook)
        if specialized is not None:
            return specialized
        return self.find_generic_extractor(workbook)

    def get_extractors(self) -> list[Extractor]:
        """Return all registered extractors.

        Returns:
            A list of all registered Extractor instances.
        """
        return list(self._extractors)

    def clear(self) -> None:
        """Clear all registered extractors."""
        self._extractors.clear()


_DEFAULT_REGISTRY: ExtractorRegistry | None = None


def get_default_registry() -> ExtractorRegistry:
    """Return the global default ExtractorRegistry populated with built-in extractors.

    The default registry includes common extractors for bank statements,
    invoices, and ledgers.
    """
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ExtractorRegistry(
            [
                ICICIBankStatementExtractor(),
                StandardBankStatementExtractor(),
                TabularInvoiceExtractor(),
                TabularLedgerExtractor(),
                AxisBankStatementExtractor(),
            ]
        )
    return _DEFAULT_REGISTRY


def register_extractor(extractor: Extractor) -> None:
    """Register an extractor into the global default registry.

    This is a convenience function that wraps the register method of the
    default registry.

    Args:
        extractor: The Extractor instance to register.
    """
    get_default_registry().register(extractor)