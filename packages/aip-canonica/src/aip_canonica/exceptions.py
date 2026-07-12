class CanonicaError(Exception):
    """Base exception for Canonica."""


class UnknownDocumentError(CanonicaError):
    """Raised when no interpreter understands a document."""
