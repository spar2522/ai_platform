"""Extractors package for the AIP Canonica project.

This package provides extractor interfaces, a registry system for managing extractors,
and built-in extractors for different data sources such as bank statements, invoices,
and ledgers. Extractors are organized into submodules for each domain (e.g., bank, invoice, ledger).
"""

from aip_canonica.extractors.bank.icici import ICICIBankStatementExtractor
from aip_canonica.extractors.bank.standard import StandardBankStatementExtractor
from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.invoice.tabular import TabularInvoiceExtractor
from aip_canonica.extractors.ledger.tabular import TabularLedgerExtractor
from aip_canonica.extractors.registry import (
    ExtractorRegistry,
    get_default_registry,
    register_extractor,
)

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