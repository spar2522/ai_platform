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

    This class allows registration of extractors and provides methods to find the
    most appropriate extractor for a given workbook. Extractors can be specialized
    or generic, with specialized extractors taking precedence over generic ones.
    """

    def __init__(self, extractors: Sequence[Extractor] | None = None) -> None:
        """Initialize the registry with a list of extractors.

        Args:
            extractors: Optional list of extractors to register. Defaults to empty.
        """
        self._extractors: list[Extractor] = list(extractors or [])

    def register(self, extractor: Extractor) -> None:
        """Register a new extraction strategy.

        Appends the provided extractor to the internal list of registered extractors.

        Args:
            extractor: The extractor to register.
        """
        self._extractors.append(extractor)

    def find_specialized_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find the first matching specialized (non-generic) extractor.

        Iterates through registered extractors and returns the first one that is not
        marked as generic and matches the provided workbook. If no such extractor is
        found, returns None.

        Args:
            workbook: The workbook to match against.

        Returns:
            The first matching specialized extractor, or None if none found.
        """
        for extractor in self._extractors:
            if getattr(extractor, "is_generic", False):
                continue
            if extractor.matches(workbook):
                return extractor
        return None

    def find_generic_extractor(self, workbook: Workbook, document_type: Any | None = None) -> Extractor | None:
        """Find the first matching generic fallback extractor.

        Iterates through registered extractors and returns the first one that is
        marked as generic, matches the provided workbook, and optionally matches the
        specified document_type. If no such extractor is found, returns None.

        Args:
            workbook: The workbook to match against.
            document_type: Optional document type to filter extractors by.

        Returns:
            The first matching generic extractor, or None if none found.
        """
        for extractor in self._extractors:
            if not getattr(extractor, "is_generic", False):
                continue
            if document_type is not None and getattr(extractor, "document_type", None) != document_type:
                continue
            if extractor.matches(workbook):
                return extractor
        return None

    def find_extractor(self, workbook: Workbook) -> Extractor | None:
        """Find the most appropriate extractor for the given workbook.

        Prioritizes specialized extractors over generic ones. If a specialized extractor
        is found, it is returned. Otherwise, a generic extractor is sought.

        Args:
            workbook: The workbook to match against.

        Returns:
            The most appropriate extractor, or None if none found.
        """
        specialized = self.find_specialized_extractor(workbook)
        if specialized:
            return specialized
        return self.find_generic_extractor(workbook)

    def clear(self) -> None:
        """Remove all registered extractors from the registry."""
        self._extractors.clear()


def get_default_registry() -> ExtractorRegistry:
    """Return a pre-configured registry with default extractors.

    Returns:
        A registry initialized with standard extractors in a defined order.
    """
    return ExtractorRegistry(
        [
            ICICIBankStatementExtractor(),
            StandardBankStatementExtractor(),
            TabularInvoiceExtractor(),
            TabularLedgerExtractor(),
            AxisBankStatementExtractor(),
        ]
    )