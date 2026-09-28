"""Public entry point for Canonica."""

from __future__ import annotations

import logging
from pathlib import Path

from aip_canonica.exceptions import UnsupportedDocumentError, ValidationError
from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.registry import ExtractorRegistry, get_default_registry
from aip_canonica.models import Workbook
from aip_canonica.models.base import CanonicalDocument
from aip_canonica.parsers.parser_factory import ParserFactory
from aip_canonica.validation.result import ValidationResult
from aip_canonica.validation.validator import validate as validate_document

logger = logging.getLogger("aip_canonica")


def parse_document(path: str | Path) -> Workbook:
    """Parse a physical document (Excel, CSV) into Canonica's raw Workbook representation."""
    target_path = Path(path)
    parser = ParserFactory.create(target_path)
    return parser.parse(target_path)


def understand(
    path: str | Path,
    *,
    extractor: Extractor | None = None,
    registry: ExtractorRegistry | None = None,
    validate: bool = False,
) -> CanonicalDocument:
    """Convert a financial document into a generic, typed canonical financial model.

    Parameters:
        path: Path to the financial document file (e.g., .xlsx, .csv).
        extractor: Optional explicit extractor instance to use.
        registry: Optional custom extractor registry (defaults to built-in registry).
        validate: If True, execute deterministic validation and raise ValidationError on failure.

    Returns:
        A strongly typed CanonicalDocument (such as BankStatement, Invoice, Ledger),
        which also provides `.as_graph()` and `.validate()`.

    Raises:
        UnsupportedDocumentError: When no registered extractor matches the document layout.
        ValidationError: When deterministic validation fails and validate=True.
    """
    target_path = Path(path)
    workbook = parse_document(target_path)
    active_registry = registry or get_default_registry()
    source_uri = str(target_path)

    # 1. Explicit extractor path
    if extractor is not None:
        logger.info("[Canonica][Match] Using explicitly provided extractor: '%s'", extractor.name)
        cand_doc = extractor.extract(workbook, source_name=source_uri)
        if validate:
            val_result = validate_document(cand_doc)
            if not val_result.is_valid:
                error_msgs = "; ".join(e.message for e in val_result.errors)
                raise ValidationError(
                    f"Deterministic validation failed for '{target_path.name}': {error_msgs}"
                )
        return cand_doc

    # 2. Specialized extractor path
    specialized = active_registry.find_specialized_extractor(workbook)
    if specialized is not None:
        logger.info(
            "[Canonica][SpecializedMatch] Found specialized extractor '%s' for '%s'.",
            specialized.name,
            target_path.name,
        )
        try:
            cand_doc = specialized.extract(workbook, source_name=source_uri)
            val_result = validate_document(cand_doc)
            if val_result.is_valid:
                return cand_doc
            error_msgs = "; ".join(e.message for e in val_result.errors)
            logger.warning(
                "[Canonica][ValidationFailed] Specialized extractor '%s' failed validation: %s. "
                "Falling back to Generic Fallback extractor...",
                specialized.name,
                error_msgs,
            )
        except Exception as exc:
            logger.warning(
                "[Canonica][ExtractorError] Specialized extractor '%s' raised exception: %s. "
                "Falling back to Generic Fallback extractor...",
                specialized.name,
                exc,
            )

    # 3. Generic fallback extractor path
    doc_type = specialized.document_type if specialized is not None else None
    generic = active_registry.find_generic_extractor(workbook, document_type=doc_type)

    if generic is not None:
        logger.info(
            "[Canonica][GenericMatch] Matched Generic Fallback extractor '%s' for '%s'.",
            generic.name,
            target_path.name,
        )
        cand_doc = generic.extract(workbook, source_name=source_uri)
        if validate:
            val_result = validate_document(cand_doc)
            if not val_result.is_valid:
                error_msgs = "; ".join(e.message for e in val_result.errors)
                raise ValidationError(
                    f"Deterministic validation failed for '{target_path.name}': {error_msgs}"
                )
        return cand_doc

    raise UnsupportedDocumentError(
        f"No matching extractor found for '{target_path.name}'."
    )


def validate(document: CanonicalDocument) -> ValidationResult:
    """Execute deterministic financial reconciliation on any canonical document."""
    return validate_document(document)
