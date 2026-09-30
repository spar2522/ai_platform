"""Canonical document types supported by Canonica.

Each document type represents a specific category of financial documents processed by Canonica.

Available types:
- BANK_STATEMENT: Represents a bank statement document.
- LEDGER: Represents a financial ledger.
- INVOICE: Represents an invoice document.
- INTEREST_CERTIFICATE: Represents a certificate of interest.
- TDS_CERTIFICATE: Represents a TDS (Tax Deducted at Source) certificate.

New types should be added following the naming convention and ensuring they are relevant to the system's scope.
"""

from enum import Enum


class DocumentType(str, Enum):
    """Initial finite set of canonical financial document types."""

    BANK_STATEMENT = "bank_statement"
    LEDGER = "ledger"
    INVOICE = "invoice"
    INTEREST_CERTIFICATE = "interest_certificate"
    TDS_CERTIFICATE = "tds_certificate"

    @classmethod
    def list_all(cls) -> list["DocumentType"]:
        """Return a list of all defined document types."""
        return list(cls)