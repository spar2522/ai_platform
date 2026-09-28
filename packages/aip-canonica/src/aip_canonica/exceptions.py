"""Exceptions for Canonica."""

from __future__ import annotations

from typing import Any


class CanonicaError(Exception):
    """Base exception for all Canonica errors."""


CanonicaException = CanonicaError


class UnsupportedDocumentError(CanonicaError):
    """Raised when no matching extractor is found for a document."""


class UnknownDocumentError(UnsupportedDocumentError):
    """Alias for backwards compatibility when no extractor understands a document."""


class ParseError(CanonicaError):
    """Raised when a document cannot be parsed into a raw source representation."""


class ExtractionError(CanonicaError):
    """Raised when extraction fails on a matched document."""


class ValidationError(CanonicaError):
    """Raised when deterministic validation on a canonical model fails."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details