"""Public entry point for Canonica."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from aip_canonica.exceptions import UnsupportedDocumentError, ValidationError
from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.registry import ExtractorRegistry, get_default_registry
from aip_canonica.models import Workbook
from aip_canonica.models.base import CanonicalDocument
from aip_canonica.parsers.parser_factory import ParserFactory
from aip_canonica.validation.result import ValidationResult
from aip_canonica.validation.validator import validate as validate_document

if TYPE_CHECKING:
    from aip_provider import AI

logger = logging.getLogger("aip_canonica")


def parse_document(path: str | Path, *, ai: AI | None = None) -> Workbook:
    """Parse a physical document (Excel, CSV, PDF) into Canonica's raw Workbook representation."""
    target_path = Path(path)
    parser = ParserFactory.create(target_path, ai=ai)
    return parser.parse(target_path)


def _try_extract_canonical_document(
    workbook: Workbook,
    active_registry: ExtractorRegistry,
    explicit_extractor: Extractor | None,
    source_uri: str,
    target_path: Path,
) -> tuple[CanonicalDocument | None, str | None, bool, list[str]]:
    """Attempt extraction and deterministic validation across explicit, specialized, and generic extractors.

    Returns:
        (document, extractor_name, is_generic, failure_reasons)
    """
    failure_reasons: list[str] = []

    # 1. Explicit extractor path
    if explicit_extractor is not None:
        logger.info("[Canonica][Match] Using explicitly provided extractor: '%s'", explicit_extractor.name)
        try:
            cand_doc = explicit_extractor.extract(workbook, source_name=source_uri)
            val_result = validate_document(cand_doc)
            if val_result.is_valid:
                return cand_doc, explicit_extractor.name, False, []
            error_msgs = "; ".join(e.message for e in val_result.errors)
            failure_reasons.append(
                f"Explicit extractor '{explicit_extractor.name}' calculation/validation failed: {error_msgs}"
            )
        except Exception as exc:
            failure_reasons.append(f"Explicit extractor '{explicit_extractor.name}' error: {exc}")
        return None, explicit_extractor.name, False, failure_reasons

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
                logger.info(
                    "[Canonica][Validation] Specialized extractor '%s' validation PASSED.",
                    specialized.name,
                )
                return cand_doc, specialized.name, False, []
            error_msgs = "; ".join(e.message for e in val_result.errors)
            failure_reasons.append(
                f"Specialized extractor '{specialized.name}' calculation/validation failed: {error_msgs}"
            )
            logger.warning(
                "[Canonica][ValidationFailed] Specialized extractor '%s' failed validation: %s. "
                "Layout may have changed. Falling back to Generic Fallback extractor...",
                specialized.name,
                error_msgs,
            )
        except Exception as exc:
            failure_reasons.append(f"Specialized extractor '{specialized.name}' extraction error: {exc}")
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
        if specialized is not None:
            logger.info(
                "[Canonica][Fallback] Specialized extractor failed; attempting Generic Fallback '%s'...",
                generic.name,
            )
        else:
            logger.info(
                "[Canonica][GenericMatch] Matched Generic Fallback extractor '%s' for '%s'.",
                generic.name,
                target_path.name,
            )

        try:
            cand_doc = generic.extract(workbook, source_name=source_uri)
            val_result = validate_document(cand_doc)
            if val_result.is_valid:
                logger.info(
                    "[Canonica][Validation] Generic Fallback extractor '%s' validation PASSED.",
                    generic.name,
                )
                return cand_doc, generic.name, True, []
            error_msgs = "; ".join(e.message for e in val_result.errors)
            failure_reasons.append(
                f"Generic fallback extractor '{generic.name}' calculation/validation failed: {error_msgs}"
            )
            logger.warning(
                "[Canonica][ValidationFailed] Generic Fallback extractor '%s' failed validation: %s",
                generic.name,
                error_msgs,
            )
        except Exception as exc:
            failure_reasons.append(f"Generic fallback extractor '{generic.name}' extraction error: {exc}")
            logger.warning(
                "[Canonica][ExtractorError] Generic Fallback extractor '%s' raised exception: %s",
                generic.name,
                exc,
            )
    else:
        failure_reasons.append(
            "Could not identify document type: No registered specialized or generic extractor matched the layout."
        )

    return None, None, False, failure_reasons


def understand(
    path: str | Path,
    *,
    extractor: Extractor | None = None,
    registry: ExtractorRegistry | None = None,
    validate: bool = False,
    ai: AI | None = None,
) -> CanonicalDocument:
    """Convert a financial document into a generic, typed canonical financial model.

    Parameters:
        path: Path to the financial document file (e.g., .xlsx, .csv, .pdf).
        extractor: Optional explicit extractor instance to use.
        registry: Optional custom extractor registry (defaults to built-in registry).
        validate: If True, execute deterministic validation and raise ValidationError on failure.
        ai: Optional configured aip-provider AI instance for Option B PDF multimodal fallback.

    Returns:
        A strongly typed CanonicalDocument (such as BankStatement, Invoice, Ledger),
        which also provides `.as_graph()` and `.validate()`.

    Raises:
        UnsupportedDocumentError: When no registered extractor matches the document layout.
        ValidationError: When deterministic validation fails and validate=True.
    """
    target_path = Path(path)
    workbook = parse_document(target_path, ai=ai)
    active_registry = registry or get_default_registry()
    source_uri = str(target_path)

    # 1. Attempt extraction on parsed workbook (Option A)
    document, matched_name, _is_generic, failure_reasons = _try_extract_canonical_document(
        workbook,
        active_registry,
        extractor,
        source_uri,
        target_path,
    )

    ai_fallback_triggered = False

    # 2. PDF Semantic / Calculation Recovery (Option B Fallback):
    # If extraction or calculation reconciliation failed on a PDF,
    # switch to Option B: AI multimodal / OCR fallback.
    if document is None and target_path.suffix.lower() == ".pdf":
        from aip_canonica.parsers.pdf_parser import PdfParser

        parser = ParserFactory.create(target_path, ai=ai)
        if isinstance(parser, PdfParser):
            reason_str = "; ".join(failure_reasons) if failure_reasons else "Semantic validation failed."
            divider = "=" * 60
            logger.info(
                "\n%s\n[Canonica][AI Fallback] Option A (Deterministic PDF extraction) failed semantic/calculation checks.\n"
                "Document: '%s'\n"
                "Issue: %s\n"
                "Switching to Option B: Engaging AI multimodal / OCR fallback via aip-provider to re-parse the PDF...\n%s",
                divider,
                target_path.name,
                reason_str,
                divider,
            )
            ai_workbook = parser.parse_ai_fallback(
                target_path,
                reason=reason_str,
                partial_workbook=workbook,
            )
            if (
                ai_workbook is not None
                and len(ai_workbook.sheets) > 0
                and any(len(s.rows) > 0 for s in ai_workbook.sheets)
            ):
                workbook = ai_workbook
                ai_doc, ai_name, ai_is_gen, ai_reasons = _try_extract_canonical_document(
                    workbook,
                    active_registry,
                    extractor,
                    source_uri,
                    target_path,
                )
                if ai_doc is not None:
                    document = ai_doc
                    matched_name = ai_name
                    ai_fallback_triggered = True
                else:
                    failure_reasons.extend(ai_reasons)

    # 3. Decision Outcomes & Logging
    if document is not None:
        val_result = validate_document(document)
        if validate and not val_result.is_valid:
            error_msgs = "; ".join(e.message for e in val_result.errors)
            logger.error(
                "[Canonica][ValidationFailed] Extractor '%s' failed validation: %s",
                matched_name,
                error_msgs,
            )
            raise ValidationError(
                f"Deterministic validation failed for '{target_path.name}': {error_msgs}"
            )

        divider = "=" * 60
        if ai_fallback_triggered:
            logger.info(
                "\n%s\n[Canonica][AI Fallback Succeeded] Document '%s' recovered via Option B (AI OCR Fallback) "
                "and validated using extractor '%s' (Validation: PASSED).\n%s",
                divider,
                target_path.name,
                matched_name,
                divider,
            )
        else:
            logger.info(
                "\n%s\n[Canonica][Deterministic] 100%% deterministic extraction (0 AI calls).\n"
                "Processed '%s' using extractor '%s' (Validation: PASSED).\n%s",
                divider,
                target_path.name,
                matched_name,
                divider,
            )
        return document

    # 4. Failure
    failure_msg = f"Failed to extract valid canonical document for '{target_path.name}'."
    if failure_reasons:
        failure_msg += f" Details: {'; '.join(failure_reasons)}"

    if validate:
        raise ValidationError(
            f"Deterministic validation failed for '{target_path.name}': {failure_msg}"
        )
    raise UnsupportedDocumentError(
        f"No matching extractor found or validation failed for '{target_path.name}'."
    )


def validate(document: CanonicalDocument) -> ValidationResult:
    """Execute deterministic financial reconciliation on any canonical document."""
    return validate_document(document)
