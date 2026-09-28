"""Extractors package exporting extractor interfaces, registry, and built-in extractors."""

# Base classes
from aip_canonica.extractors.base import Extractor

# Registry
from aip_canonica.extractors.registry import (
    ExtractorRegistry,
    get_default_registry,
    register_extractor,
)

# Extractors
from aip_canonica.extractors.bank.icici import ICICIBankStatementExtractor
from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.extractors.invoice.tabular import TabularInvoiceExtractor
from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor

__all__ = [
    "Extractor",
    "ExtractorRegistry",
    "ICICIBankStatementExtractor",
    "StandardBankStatementExtractor",
    "TabularInvoiceExtractor",
    "TabularLedgerExtractor",
    "get_default_registry",
    "register_extractor",
]