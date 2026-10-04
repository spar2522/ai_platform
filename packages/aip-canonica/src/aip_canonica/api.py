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
    learning_mode: bool = False,
    ai: AI | None = None,
) -> CanonicalDocument:
    """Convert a financial document into a generic, typed canonical financial model.

    Parameters:
        path: Path to the financial document file (e.g., .xlsx, .csv, .pdf).
        extractor: Optional explicit extractor instance to use.
        registry: Optional custom extractor registry (defaults to built-in registry).
        validate: If True, execute deterministic validation and raise ValidationError on failure.
        learning_mode: If True, engages the offline AI StrategyLearner when generic fallback
            is used or when extraction fails, providing a report and candidate extractor code.
        ai: Optional configured aip-provider AI instance for learning mode or Option B PDF fallback.

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
    document, matched_name, is_generic, failure_reasons = _try_extract_canonical_document(
        workbook,
        active_registry,
        extractor,
        source_uri,
        target_path,
    )

    ai_fallback_triggered = False

    def _is_complete_and_valid(doc: CanonicalDocument | None) -> bool:
        if doc is None:
            return False
        from aip_canonica.models.bank_statement import BankStatement
        from aip_canonica.models.invoice import Invoice
        from aip_canonica.models.ledger import Ledger

        if isinstance(doc, BankStatement) and not doc.transactions:
            return False
        if isinstance(doc, Invoice) and not doc.lines:
            return False
        if isinstance(doc, Ledger) and not doc.entries:
            return False
        return validate_document(doc).is_valid

    # 2. PDF Semantic / Calculation Recovery (Option B Fallback):
    # If extraction or calculation reconciliation failed on a PDF,
    # and the user explicitly supplied an AI instance, engage AI multimodal / OCR fallback.
    if target_path.suffix.lower() == ".pdf" and not _is_complete_and_valid(document):
        total_rows = sum(len(s.rows) for s in workbook.sheets)
        total_chars = sum(
            len(str(c.value or ""))
            for s in workbook.sheets
            for r in s.rows
            for c in r.cells
            if c.value is not None
        )
        has_sufficient_text = total_rows >= 3 and total_chars >= 50

        if learning_mode and has_sufficient_text:
            logger.info(
                "\n[Canonica][Flow] Deterministic workbook parsing succeeded (%d rows, %d chars). "
                "The PDF is digital text (not a scanned image). "
                "Bypassing Option B (AI OCR Fallback) and routing directly to Option C (AI Strategy Learner) "
                "to analyze this layout and synthesize a specialized extractor.",
                total_rows,
                total_chars,
            )
        elif ai is None:
            logger.info(
                "[Canonica][Notice] Option A deterministic PDF extraction did not produce a complete valid document. "
                "No AI instance was provided (ai=None), so AI OCR fallback was not attempted (0 AI calls)."
            )
        else:
            from aip_canonica.parsers.pdf_parser import PdfParser

            parser = ParserFactory.create(target_path, ai=ai)
            if isinstance(parser, PdfParser):
                reason_str = (
                    "; ".join(failure_reasons)
                    if failure_reasons
                    else "Deterministic extraction produced incomplete or unvalidated data."
                )
                divider = "=" * 60
                logger.info(
                    "\n%s\n[Canonica][AI Fallback] Option A (Deterministic PDF extraction) failed semantic/calculation checks.\n"
                    "Document: '%s'\n"
                    "Issue: %s\n"
                    "Engaging Option B: AI multimodal / OCR fallback using configured AI provider...\n%s",
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
                    if ai_doc is not None and _is_complete_and_valid(ai_doc):
                        document = ai_doc
                        matched_name = ai_name
                        is_generic = ai_is_gen
                        ai_fallback_triggered = True
                    else:
                        failure_reasons.extend(ai_reasons)

    # 3. Decision Outcomes & Logging
    if document is not None:
        from aip_canonica.audit import get_ai_connectivity_info

        effective_ai = ai if ai_fallback_triggered else None
        audit_info = get_ai_connectivity_info(effective_ai)
        audit_info["ai_used"] = bool(ai_fallback_triggered)
        audit_info["mode"] = "ai_multimodal_fallback" if ai_fallback_triggered else "deterministic"
        document.metadata["ai_audit"] = audit_info

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

        # Specialized / Explicit Extractor
        if not is_generic:
            divider = "=" * 60
            if ai_fallback_triggered:
                logger.info(
                    "\n%s\n[Canonica][AI Fallback Succeeded] Document '%s' recovered via Option B (AI OCR Fallback) "
                    "and validated using specialized extractor '%s' (Validation: PASSED).\n%s",
                    divider,
                    target_path.name,
                    matched_name or "specialized",
                    divider,
                )
            else:
                logger.info(
                    "\n%s\n[Canonica][Deterministic] 100%% deterministic extraction (0 AI calls, learning_mode=OFF).\n"
                    "Processed using specialized extractor '%s' (Validation: PASSED).\n%s",
                    divider,
                    matched_name or "specialized",
                    divider,
                )
            return document

        # Generic Fallback Extractor Succeeded
        if not learning_mode:
            divider = "=" * 60
            if ai_fallback_triggered:
                logger.warning(
                    "\n%s\n[Canonica][AI Fallback Succeeded] Document '%s' parsed via Option B (AI OCR Fallback) "
                    "and validated using Generic Fallback extractor '%s' (Validation: PASSED).\n"
                    "Note: A specialized extractor is not yet registered for this layout.\n%s",
                    divider,
                    target_path.name,
                    matched_name or "generic",
                    divider,
                )
            else:
                logger.warning(
                    "\n%s\n[Canonica][Notice] No AI was used (learning_mode=OFF).\n"
                    "Document '%s' processed deterministically using Generic Fallback extractor '%s' (Validation: PASSED).\n"
                    "Note: A specialized extractor is not yet registered for this layout. "
                    "Enabling learning_mode=True would analyze if richer bank-specific metadata (e.g., counterparties, customer codes, branch details) can be extracted.\n%s",
                    divider,
                    target_path.name,
                    matched_name or "generic",
                    divider,
                )
            return document
        else:
            if ai is None:
                raise ValueError(
                    "learning_mode=True requires an AI instance to inspect layout and synthesize extractor code. "
                    "Pass an explicit ai instance (e.g. ai=AI.local() or ai=AI.gemini(...))."
                )
            divider = "=" * 60
            logger.info(
                "\n%s\n[Canonica][AI Learner] Generic extraction passed with learning_mode=True. "
                "Engaging AI Strategy Learner to analyze if a specialized extractor would capture richer metadata...\n%s",
                divider,
                divider,
            )
            from aip_canonica.audit import get_ai_connectivity_info, log_api_notice
            from aip_canonica.learning.learner import StrategyLearner

            log_api_notice(
                purpose="Option C AI Strategy Learner Analysis",
                ai=ai,
                document_name=target_path.name,
                extra_details="Analyzing document structure to synthesize candidate extractor.",
            )

            learner = StrategyLearner(ai=ai)
            report = learner.analyze_and_report(
                workbook,
                document_name=target_path.name,
                baseline_document=document,
                name=f"{target_path.stem}_strategy",
            )
            logger.info("\n%s", report.summary())

            audit_info = get_ai_connectivity_info(ai)
            audit_info["ai_used"] = True
            audit_info["mode"] = "learning_mode"
            document.metadata["ai_audit"] = audit_info

            return document

    # 4. Extraction / Validation Failed Entirely
    failure_msg = f"Failed to extract valid canonical document for '{target_path.name}'."
    if failure_reasons:
        failure_msg += f" Details: {'; '.join(failure_reasons)}"

    if not learning_mode:
        divider = "=" * 60
        logger.error(
            "\n%s\n[Canonica][Error] %s No valid extractor match or validation checks failed.\n"
            "No AI was used (learning_mode=OFF). Enable learning_mode=True to inspect layout with AI and synthesize a specialized extractor.\n%s",
            divider,
            failure_msg,
            divider,
        )
        if validate:
            raise ValidationError(
                f"Deterministic validation failed for '{target_path.name}': {failure_msg}"
            )
        raise UnsupportedDocumentError(
            f"No matching extractor found or validation failed for '{target_path.name}'."
        )
    else:
        if ai is None:
            raise ValueError(
                "learning_mode=True requires an AI instance to inspect layout and synthesize extractor code. "
                "Pass an explicit ai instance (e.g. ai=AI.local() or ai=AI.gemini(...))."
            )
        divider = "=" * 60
        logger.info(
            "\n%s\n[Canonica][AI Learner] Extraction failed with learning_mode=True. "
            "Engaging AI Strategy Learner to inspect layout and synthesize candidate extractor...\n%s",
            divider,
            divider,
        )
        from aip_canonica.audit import log_api_notice
        from aip_canonica.learning.learner import StrategyLearner

        log_api_notice(
            purpose="Option C AI Strategy Learner Analysis",
            ai=ai,
            document_name=target_path.name,
            extra_details="Analyzing document structure to synthesize candidate extractor.",
        )

        learner = StrategyLearner(ai=ai)
        report = learner.analyze_and_report(
            workbook,
            document_name=target_path.name,
            baseline_document=None,
            name=f"{target_path.stem}_strategy",
        )
        logger.info("\n%s", report.summary())
        strat_name = report.strategy.name if report.strategy else "candidate_strategy"
        raise ValidationError(
            f"Extraction failed for '{target_path.name}'. AI Strategy Learner synthesized candidate strategy: '{strat_name}'.",
            details=report,
        )


def validate(document: CanonicalDocument) -> ValidationResult:
    """Execute deterministic financial reconciliation on any canonical document."""
    return validate_document(document)
