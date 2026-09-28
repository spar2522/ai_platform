"""Canonical document types supported by Canonica."""

from enum import Enum


class DocumentType(str, Enum):
    """Initial finite set of canonical financial document types."""

    BANK_STATEMENT = "bank_statement"
    LEDGER = "ledger"
    INVOICE = "invoice"
    INTEREST_CERTIFICATE = "interest_certificate"
    TDS_CERTIFICATE = "tds_certificate"
