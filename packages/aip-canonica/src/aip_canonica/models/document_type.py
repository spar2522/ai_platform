"""Canonical document types supported by Canonica.

This module defines an enumeration of document types recognized by the Canonica system. These types are used to categorize and process financial documents.
"""

from enum import Enum


class DocumentType(str, Enum):
    """Initial finite set of canonical financial document types.

    Each member represents a specific type of financial document, with the value being the lowercase string representation used in the system.
    """

    BANK_STATEMENT = "bank_statement"
    LEDGER = "ledger"
    INVOICE = "invoice"
    INTEREST_CERTIFICATE = "interest_certificate"
    TDS_CERTIFICATE = "tds_certificate"