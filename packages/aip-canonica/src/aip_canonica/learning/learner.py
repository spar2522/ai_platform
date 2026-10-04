"""AI-assisted strategy learner for unknown document families.

AI is used strictly during the offline/learning phase to discover structural anchors
and column mappings. Runtime execution remains 100% deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

from aip_canonica.learning.strategy import LearnedStrategy, LearningReport
from aip_canonica.models.base import CanonicalDocument
from aip_canonica.models.document_type import DocumentType
from aip_canonica.models import Workbook

if TYPE_CHECKING:
    from aip_provider import AI


class StrategyLearner:
    """Uses aip-provider to learn extraction strategies for novel document layouts."""

    def __init__(self, ai: AI | None = None) -> None:
        self._ai = ai

    def _get_ai(self) -> AI:
        if self._ai is None:
            from aip_provider import AI

            self._ai = AI.local()
        return self._ai

    def _summarize_workbook_sample(self, workbook: Workbook, max_rows: int = 25) -> str:
        """Create a compact sample representation of the workbook for AI inspection."""
        lines: list[str] = []
        for sheet in workbook.sheets:
            lines.append(f"--- Sheet: {sheet.name} ---")
            for row in sheet.rows[:max_rows]:
                vals = [str(c.value).strip() for c in row.cells if c.value is not None and str(c.value).strip()]
                if vals:
                    lines.append(f"Row {row.index}: " + " | ".join(vals[:12]))
        return "\n".join(lines)

    def _find_related_extractor(self, workbook: Workbook) -> tuple[Any | None, str]:
        """Discover if an existing registered specialized extractor already represents this institution."""
        import inspect
        from aip_canonica.extractors.registry import get_default_registry

        registry = get_default_registry()
        # 1. Direct matches() evaluation on specialized extractors
        for extractor in registry.get_extractors():
            if getattr(extractor, "is_generic", False):
                continue
            try:
                if extractor.matches(workbook):
                    try:
                        code = inspect.getsource(extractor.__class__)
                        return extractor, code
                    except Exception:
                        return extractor, f"# Class {extractor.__class__.__name__} is registered."
            except Exception:
                pass

        # 2. Key institution tokens check in workbook sample
        sample_text = self._summarize_workbook_sample(workbook).lower()
        for extractor in registry.get_extractors():
            if getattr(extractor, "is_generic", False):
                continue
            name_tokens = [
                tok
                for tok in extractor.name.lower().split("_")
                if len(tok) >= 4 and tok not in {"bank", "statement", "invoice", "ledger", "tabular", "standard"}
            ]
            if any(tok in sample_text for tok in name_tokens):
                try:
                    code = inspect.getsource(extractor.__class__)
                    return extractor, code
                except Exception:
                    return extractor, f"# Class {extractor.__class__.__name__} is registered."

        return None, ""

    async def learn_from_workbook(
        self,
        workbook: Workbook,
        *,
        name: str = "learned_strategy",
    ) -> LearnedStrategy:
        """Analyze document sample via aip-provider AI to infer structural anchors, layout paradigms, and evolutionary strategy."""
        ai = self._get_ai()
        sample_text = self._summarize_workbook_sample(workbook)
        existing_extractor, existing_code = self._find_related_extractor(workbook)

        system_prompt = (
            "You are an expert financial document layout analyzer and software architect for Canonica. "
            "Analyze the provided sample rows from a financial document and determine:\n"
            "1. Canonical document type: one of [bank_statement, ledger, invoice, interest_certificate, tds_certificate].\n"
            "2. Physical layout paradigm:\n"
            "   - 'flat_tabular': 1 row = 1 complete transaction/record (common in spreadsheets/CSVs).\n"
            "   - 'multiline_block': records wrap across 2+ consecutive rows (common in PDFs where date, narration, and amount/balance are stacked).\n"
            "   - 'key_value_form': form-based fields.\n"
            "3. Evolution Strategy:\n"
            "   - If an existing extractor for this institution is provided in the prompt, classify strategy_action as 'evolve_existing'.\n"
            "   - Propose how to extend the existing extractor so it supports BOTH the old layout and this new layout variant under one unified class.\n"
            "   - If no existing extractor is provided, classify strategy_action as 'create_new'.\n"
            "4. Return strictly valid JSON."
        )

        existing_section = ""
        if existing_extractor and existing_code:
            existing_section = f"""
======================================================================
EXISTING REGISTERED EXTRACTOR FOR THIS INSTITUTION:
Extractor Name: {existing_extractor.name}
Class Name: {existing_extractor.__class__.__name__}
Source Code:
{existing_code}
======================================================================
Note: An extractor already exists for this financial institution/family.
If this new document represents a layout variant (e.g. wrapped multiline PDF vs flat tabular spreadsheet),
we must EVOLVE this existing extractor to support BOTH variants seamlessly rather than creating a competing duplicate.
"""

        target_name = existing_extractor.name if existing_extractor else name
        prompt = f"""{existing_section}
Analyze this document sample:

{sample_text}

Respond ONLY with a JSON object with this schema:
{{
    "name": "{target_name}",
    "document_type": "bank_statement" | "ledger" | "invoice" | "interest_certificate" | "tds_certificate",
    "layout_type": "flat_tabular" | "multiline_block" | "key_value_form",
    "strategy_action": "create_new" | "evolve_existing",
    "related_extractor_name": "{existing_extractor.name if existing_extractor else ''}",
    "anchor_keywords": ["keyword1", "keyword2"],
    "table_header_keywords": ["header1", "header2"],
    "column_mapping": {{"standard_field": "header_in_document"}},
    "metadata_fields": {{"field_name": "label_in_document"}},
    "block_delimiters": {{
        "record_start_regex": "^(\\\\d{{2}}-\\\\d{{2}}-\\\\d{{4}})",
        "amount_balance_pattern": "(\\\\d+\\\\.\\\\d{{2}})"
    }},
    "notes": "explanation of detected layout and evolution strategy"
}}
"""
        response = await ai.generate(prompt=prompt, system_prompt=system_prompt)
        from aip_canonica.audit import log_token_usage

        log_token_usage(response, title=f"AI Strategy Learner ({response.model})")
        content = response.text.strip()

        # Clean JSON markdown fences if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback to safe defaults if AI returned malformed text
            data = {
                "name": target_name,
                "document_type": "bank_statement",
                "notes": content[:100],
            }

        doc_type_val = data.get("document_type", "bank_statement").lower()
        try:
            doc_type = DocumentType(doc_type_val)
        except ValueError:
            doc_type = DocumentType.BANK_STATEMENT

        layout_type = str(data.get("layout_type", "flat_tabular"))
        strategy_action = str(
            data.get("strategy_action", "evolve_existing" if existing_extractor else "create_new")
        )
        related_name = data.get("related_extractor_name") or (existing_extractor.name if existing_extractor else None)

        return LearnedStrategy(
            name=data.get("name", target_name),
            document_type=doc_type,
            anchor_keywords=list(data.get("anchor_keywords", [])),
            table_header_keywords=list(data.get("table_header_keywords", [])),
            column_mapping=dict(data.get("column_mapping", {})),
            metadata_fields=dict(data.get("metadata_fields", {})),
            layout_type=layout_type,
            evolution_mode=strategy_action,
            related_extractor_name=related_name,
            block_delimiters=dict(data.get("block_delimiters", {})),
            notes=str(data.get("notes", "")),
        )

    async def analyze_and_report_async(
        self,
        workbook: Workbook,
        *,
        document_name: str = "document",
        baseline_document: CanonicalDocument | None = None,
        name: str = "candidate_extractor",
        output_dir: Path | str | None = None,
    ) -> LearningReport:
        """Analyze workbook using AI, compare with standard baseline, save extractor and detailed report."""
        import logging
        logger = logging.getLogger("aip_canonica")

        strategy = await self.learn_from_workbook(workbook, name=name)

        # Determine baseline extracted fields
        baseline_fields: list[str] = []
        if baseline_document is not None:
            baseline_fields.extend(["transactions", "opening_balance", "closing_balance", "dates"])
            if getattr(baseline_document, "account_number", None):
                baseline_fields.append("account_number")
            if getattr(baseline_document, "institution_name", None):
                baseline_fields.append("institution_name")
            if getattr(baseline_document, "account_holder", None):
                baseline_fields.append("account_holder")
            if getattr(baseline_document, "invoice_number", None):
                baseline_fields.append("invoice_number")
            if getattr(baseline_document, "lines", None):
                baseline_fields.append("lines")

        ai_fields = list(strategy.metadata_fields.keys())
        additional_fields = [f for f in ai_fields if f not in baseline_fields]

        existing_extractor, existing_code = self._find_related_extractor(workbook)

        if strategy.evolution_mode == "evolve_existing":
            recommendation = "evolve_existing_extractor"
            code_snippet = self.generate_extractor_code(strategy, existing_code=existing_code)
        elif len(additional_fields) > 0 or baseline_document is None:
            recommendation = "create_specialized_extractor"
            code_snippet = self.generate_extractor_code(strategy)
        else:
            recommendation = "use_generic"
            code_snippet = ""

        # Determine target output directory for generated artifacts
        out_dir = Path(output_dir) if output_dir else Path.cwd() / ".canonica" / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)

        clean_slug = re.sub(r"[^a-zA-Z0-9_]+", "_", strategy.name.lower()).strip("_")
        extractor_path: Path | None = None
        report_path: Path | None = None

        if code_snippet:
            extractor_path = out_dir / f"{clean_slug}_extractor.py"
            extractor_path.write_text(code_snippet, encoding="utf-8")

        # Always save detailed markdown report
        report_path = out_dir / f"{clean_slug}_report.md"
        report_content = self.generate_detailed_markdown_report(
            document_name=document_name,
            strategy=strategy,
            baseline_fields=baseline_fields,
            ai_fields=ai_fields,
            additional_fields=additional_fields,
            recommendation=recommendation,
            code_snippet=code_snippet,
            extractor_path=extractor_path,
        )
        report_path.write_text(report_content, encoding="utf-8")

        report = LearningReport(
            document_name=document_name,
            detected_document_type=strategy.document_type,
            baseline_fields_extracted=baseline_fields,
            ai_discovered_fields=ai_fields,
            additional_metadata_fields=additional_fields,
            recommended_action=recommendation,
            strategy=strategy,
            generated_code_snippet=code_snippet,
            extractor_file_path=extractor_path,
            report_file_path=report_path,
            notes=strategy.notes,
        )

        divider = "=" * 60
        logger.info(divider)
        logger.info(
            "[Canonica][AI Learner] Layout analysis complete. Extra metadata: %s. Recommendation: %s",
            report.additional_metadata_fields or "None",
            report.recommended_action.upper(),
        )
        logger.info(divider)
        return report

    def analyze_and_report(
        self,
        workbook: Workbook,
        *,
        document_name: str = "document",
        baseline_document: CanonicalDocument | None = None,
        name: str = "candidate_extractor",
    ) -> LearningReport:
        """Synchronous wrapper for analyze_and_report_async."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    self.analyze_and_report_async(
                        workbook,
                        document_name=document_name,
                        baseline_document=baseline_document,
                        name=name,
                    ),
                ).result()
        return asyncio.run(
            self.analyze_and_report_async(
                workbook,
                document_name=document_name,
                baseline_document=baseline_document,
                name=name,
            )
        )

    def generate_extractor_code(
        self, strategy: LearnedStrategy, existing_code: str | None = None
    ) -> str:
        """Synthesize Python extractor skeleton code based on learned strategy and evolution mode."""
        clean_name = "".join(part.capitalize() for part in strategy.name.split("_"))
        if not clean_name.endswith("Extractor"):
            clean_name += "Extractor"

        anchors_repr = repr(strategy.anchor_keywords)
        headers_repr = repr(strategy.table_header_keywords)
        col_map_repr = repr(strategy.column_mapping)
        meta_repr = repr(strategy.metadata_fields)
        rec_start = strategy.block_delimiters.get("record_start_regex", r"^\d{2}-\d{2}-\d{4}")

        if strategy.evolution_mode == "evolve_existing" and existing_code:
            return f'''# ======================================================================
# EVOLVED UNIFIED EXTRACTOR: {clean_name}
# Synthesized by Canonica Evolutionary Strategy Learner
# Extends existing institution extractor with '{strategy.layout_type}' layout variant.
# ======================================================================

{existing_code}

# --- EXTENSION SUB-STRATEGY SPECIFICATION FOR '{strategy.layout_type}' ---
# Table headers: {headers_repr}
# Column mappings: {col_map_repr}
# Record start regex: r"{rec_start}"
# Layout metadata fields: {meta_repr}
'''

        if strategy.layout_type == "multiline_block":
            return f'''"""Auto-synthesized deterministic multiline block extractor for '{strategy.name}' layout."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Any

from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.helpers import (
    extract_counterparty_from_narration,
    normalize_text,
    parse_decimal,
)
from aip_canonica.models import DocumentType, Workbook, Sheet, CanonicalDocument
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


class {clean_name}:
    """Auto-synthesized multiline block extractor for '{strategy.name}' layout."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.{strategy.document_type.name}

    @property
    def name(self) -> str:
        return "{strategy.name}"

    @property
    def is_generic(self) -> bool:
        return False

    def matches(self, workbook: Workbook) -> bool:
        anchors = {anchors_repr}
        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                row_text = " ".join(str(c.value or "").lower() for c in row.cells if c.value is not None)
                if any(a.lower() in row_text for a in anchors):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        sheet = workbook.sheets[0]
        record_regex = re.compile(r"{rec_start}")

        # 1. Opening & Closing Balances
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None
        for row in sheet.rows:
            joined = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)
            if "opening balance" in joined.lower():
                m = re.search(r"(\\d+\\.\\d{{2}})", joined)
                if m:
                    opening_balance = Decimal(m.group(1))
            elif "closing balance" in joined.lower():
                m = re.search(r"(\\d+\\.\\d{{2}})", joined)
                if m:
                    closing_balance = Decimal(m.group(1))

        # 2. Iterate multiline transaction blocks
        transactions: list[Transaction] = []
        current_balance = opening_balance
        i = 0

        while i < len(sheet.rows):
            row = sheet.rows[i]
            joined = " ".join(str(c.value).strip() for c in row.cells if c.value is not None)
            if any(stop in joined.lower() for stop in ["transaction total", "closing balance", "legend", "unless"]):
                break

            m_dt = record_regex.search(joined)
            if m_dt:
                txn_date = m_dt.group(0)
                narration_parts: list[str] = []
                active_cells = [c.location for c in row.cells if c.value is not None]
                bal_val: Decimal | None = None
                amt_val: Decimal | None = None

                for cell in row.cells:
                    val = str(cell.value or "").strip()
                    if not val:
                        continue
                    m_bal = re.match(r"^(\\d+\\.\\d{{2}})\\s+\\d+$", val)
                    if m_bal:
                        bal_val = Decimal(m_bal.group(1))
                        continue
                    m_amt = re.match(r"^(\\d+\\.\\d{{2}})$", val)
                    if m_amt:
                        amt_val = Decimal(m_amt.group(1))
                        continue
                    cleaned = val
                    if cleaned.startswith(txn_date):
                        cleaned = cleaned[len(txn_date):].strip()
                    if cleaned:
                        narration_parts.append(cleaned)

                if bal_val is None:
                    while i + 1 < len(sheet.rows):
                        i += 1
                        sub_row = sheet.rows[i]
                        sub_joined = " ".join(str(c.value).strip() for c in sub_row.cells if c.value is not None)
                        if any(stop in sub_joined.lower() for stop in ["transaction total", "closing balance"]):
                            break
                        for c in sub_row.cells:
                            if c.value is not None:
                                active_cells.append(c.location)
                            val = str(c.value or "").strip()
                            if not val:
                                continue
                            m_bal = re.match(r"^(\\d+\\.\\d{{2}})\\s+\\d+$", val)
                            if m_bal:
                                bal_val = Decimal(m_bal.group(1))
                                continue
                            m_amt = re.match(r"^(\\d+\\.\\d{{2}})$", val)
                            if m_amt:
                                amt_val = Decimal(m_amt.group(1))
                                continue
                            narration_parts.append(val)
                        if bal_val is not None:
                            break

                if bal_val is not None:
                    if current_balance is not None:
                        if bal_val > current_balance:
                            direction = TransactionDirection.CREDIT
                            computed_amt = bal_val - current_balance
                        else:
                            direction = TransactionDirection.DEBIT
                            computed_amt = current_balance - bal_val
                        amount = amt_val if amt_val is not None else computed_amt
                    else:
                        amount = amt_val or Decimal("0")
                        direction = TransactionDirection.CREDIT

                    current_balance = bal_val
                    narration = " ".join(narration_parts).strip()
                    cp_name = extract_counterparty_from_narration(narration)
                    counterparty = Party(id=f"party:{{re.sub(r'[^a-zA-Z0-9]+', '_', cp_name.lower())}}", name=cp_name) if cp_name else None

                    transactions.append(
                        Transaction(
                            id=f"txn:{strategy.name}:{{len(transactions) + 1}}",
                            date=txn_date,
                            amount=amount,
                            direction=direction,
                            currency="INR",
                            narration=narration,
                            balance=bal_val,
                            counterparty=counterparty,
                            provenance=Provenance.from_cells(active_cells, source=source_name, sheet=sheet.name, row=row.index),
                        )
                    )
            i += 1

        if closing_balance is None:
            closing_balance = current_balance

        return BankStatement(
            id=f"stmt:{strategy.name}:statement",
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=Provenance(source=source_name, sheet=sheet.name, metadata={{"extractor": self.name}}),
            metadata={{"layout": "multiline_block", "synthesized": True}},
        )
'''

        return f'''"""Auto-synthesized deterministic tabular extractor for '{strategy.name}'."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Any

from aip_canonica.extractors.base import Extractor
from aip_canonica.extractors.helpers import (
    extract_counterparty_from_narration,
    normalize_text,
    parse_decimal,
)
from aip_canonica.models import DocumentType, Workbook, Sheet, CanonicalDocument
from aip_canonica.models.bank_statement import BankStatement, Transaction
from aip_canonica.models.base import DatePeriod, TransactionDirection
from aip_canonica.models.party import Account, Party
from aip_canonica.models.provenance import Provenance


class {clean_name}:
    """Auto-synthesized deterministic tabular extractor for '{strategy.name}' layout."""

    @property
    def document_type(self) -> DocumentType:
        return DocumentType.{strategy.document_type.name}

    @property
    def name(self) -> str:
        return "{strategy.name}"

    @property
    def is_generic(self) -> bool:
        return False

    def matches(self, workbook: Workbook) -> bool:
        anchors = {anchors_repr}
        headers = {headers_repr}
        for sheet in workbook.sheets:
            for row in sheet.rows[:35]:
                row_text = " ".join(str(c.value or "").lower() for c in row.cells if c.value is not None)
                if any(a.lower() in row_text for a in anchors):
                    return True
                if headers and all(h.lower() in row_text for h in headers[:3]):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> BankStatement:
        sheet = workbook.sheets[0]
        col_mapping_spec = {col_map_repr}
        meta_spec = {meta_repr}

        # 1. Locate header row and map column indices
        header_row_idx: int | None = None
        col_map: dict[str, int] = {{}}

        for row in sheet.rows[:40]:
            row_texts = [str(c.value or "").strip().lower() for c in row.cells if c.value is not None]
            matches_count = 0
            for canonical_key, doc_header in col_mapping_spec.items():
                if any(doc_header.lower() in t for t in row_texts):
                    matches_count += 1
            if matches_count >= 2:
                header_row_idx = row.index
                for c_idx, cell in enumerate(row.cells):
                    txt = str(cell.value or "").strip().lower()
                    for canonical_key, doc_header in col_mapping_spec.items():
                        if doc_header.lower() in txt or txt in doc_header.lower():
                            col_map[canonical_key] = c_idx
                break

        if header_row_idx is None:
            raise ValueError(f"Could not locate table header in '{strategy.name}' layout.")

        # 2. Extract institution and account metadata
        account_number = ""
        holder_name = ""
        for row in sheet.rows[:header_row_idx]:
            for cell in row.cells:
                val = str(cell.value or "").strip()
                if "account" in val.lower() and not account_number:
                    m = re.search(r"(?:a/c|account|no)[^0-9]*([0-9A-Za-z]+)", val, re.IGNORECASE)
                    if m:
                        account_number = m.group(1)
                if "name" in val.lower() and not holder_name:
                    m = re.search(r"name\\s*[:-]+\\s*(.+)", val, re.IGNORECASE)
                    if m:
                        holder_name = m.group(1)

        # 3. Extract transaction rows
        transactions: list[Transaction] = []
        opening_balance: Decimal | None = None
        closing_balance: Decimal | None = None

        for row in sheet.rows:
            if row.index <= header_row_idx:
                continue

            row_str = " ".join(str(c.value or "").strip() for c in row.cells if c.value is not None)
            if not row_str or any(stop in row_str.lower() for stop in ["page total", "closing balance", "legend", "unless"]):
                break

            def get_val(key: str) -> str:
                idx = col_map.get(key)
                if idx is not None and idx < len(row.cells):
                    v = row.cells[idx].value
                    return str(v).strip() if v is not None else ""
                return ""

            txn_date = get_val("date") or get_val("txn_date")
            if not txn_date or not re.search(r"\\d", txn_date):
                continue

            narration = get_val("description") or get_val("narration") or get_val("particulars")
            debit_str = get_val("debit") or get_val("withdrawal")
            credit_str = get_val("credit") or get_val("deposit")
            balance_str = get_val("balance")

            debit_dec = parse_decimal(debit_str, default=Decimal("0")) or Decimal("0")
            credit_dec = parse_decimal(credit_str, default=Decimal("0")) or Decimal("0")
            balance_dec = parse_decimal(balance_str)

            if debit_dec > Decimal("0"):
                amount = debit_dec
                direction = TransactionDirection.DEBIT
            elif credit_dec > Decimal("0"):
                amount = credit_dec
                direction = TransactionDirection.CREDIT
            else:
                continue

            if opening_balance is None and balance_dec is not None:
                if direction == TransactionDirection.CREDIT:
                    opening_balance = balance_dec - amount
                else:
                    opening_balance = balance_dec + amount

            closing_balance = balance_dec

            active_cells = [c.location for c in row.cells if c.value is not None]
            provenance = Provenance.from_cells(
                active_cells,
                source=source_name,
                sheet=sheet.name,
                row=row.index,
            )

            cp_name = extract_counterparty_from_narration(narration)
            counterparty = Party(id=f"party:{{re.sub(r'[^a-zA-Z0-9]+', '_', cp_name.lower())}}", name=cp_name) if cp_name else None

            transactions.append(
                Transaction(
                    id=f"txn:{strategy.name}:{{len(transactions) + 1}}",
                    date=txn_date,
                    amount=amount,
                    direction=direction,
                    currency="INR",
                    narration=narration,
                    balance=balance_dec,
                    counterparty=counterparty,
                    provenance=provenance,
                )
            )

        account = Account(
            id=f"acc:{strategy.name}:{{account_number or 'default'}}",
            account_number=account_number or "UNKNOWN",
            currency="INR",
        ) if account_number else None

        holder = Party(
            id=f"party:{{re.sub(r'[^a-zA-Z0-9]+', '_', holder_name.lower())}}",
            name=holder_name,
        ) if holder_name else None

        return BankStatement(
            id=f"stmt:{strategy.name}:{{account_number or 'default'}}",
            account=account,
            holder=holder,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            currency="INR",
            transactions=transactions,
            provenance=Provenance(source=source_name, sheet=sheet.name, metadata={{"extractor": self.name}}),
            metadata={{"layout": "tabular", "synthesized": True}},
        )
'''

    def generate_detailed_markdown_report(
        self,
        *,
        document_name: str,
        strategy: LearnedStrategy,
        baseline_fields: list[str],
        ai_fields: list[str],
        additional_fields: list[str],
        recommendation: str,
        code_snippet: str = "",
        extractor_path: Path | None = None,
    ) -> str:
        """Generate comprehensive markdown documentation report for learned strategy."""
        extractor_link = (
            f"[{extractor_path.name}]({extractor_path.as_uri()})"
            if extractor_path
            else "N/A (Generic fallback sufficient)"
        )
        col_rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in strategy.column_mapping.items())
        meta_rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in strategy.metadata_fields.items())
        delim_rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in strategy.block_delimiters.items())

        return f"""# Canonica AI Strategy Learning Report: {document_name}

- **Detected Document Type**: `{strategy.document_type.value}`
- **Layout Paradigm**: `{strategy.layout_type}`
- **Evolution Action**: `{strategy.evolution_mode.upper()}`
- **Target Institution Extractor**: `{strategy.related_extractor_name or strategy.name}`
- **Recommendation**: `{recommendation.upper()}`
- **Generated Extractor File**: {extractor_link}

---

## 1. Discovered Structural Anchors & Table Headers
- **Anchor Keywords**: {", ".join(f"`{k}`" for k in strategy.anchor_keywords) or "None"}
- **Table Header Keywords**: {", ".join(f"`{k}`" for k in strategy.table_header_keywords) or "None"}

## 2. Layout Delimiters & Multi-Line Rules
| Delimiter / Pattern | Value |
| :--- | :--- |
{delim_rows or "| None | None |"}

## 3. Discovered Column Mappings
| Canonical Field | Document Header / Label |
| :--- | :--- |
{col_rows or "| None | None |"}

## 4. Discovered Metadata Fields
| Field | Label / Source in Document |
| :--- | :--- |
{meta_rows or "| None | None |"}

## 5. Metadata Density Comparison
- **Standard Baseline Extracted Fields**: {", ".join(f"`{f}`" for f in baseline_fields) or "None"}
- **AI Discovered Metadata Fields**: {", ".join(f"`{f}`" for f in ai_fields) or "None"}
- **Richer Metadata Fields**: {", ".join(f"`{f}`" for f in additional_fields) or "None"}

## 6. Layout Observations & Evolution Rationale
{strategy.notes or "No additional notes recorded."}

## 7. Generated Extractor Implementation Code
```python
{code_snippet or "# Generic fallback extractor is sufficient for this layout."}
```
"""
