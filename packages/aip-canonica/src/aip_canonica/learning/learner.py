"""AI-assisted strategy learner for unknown document families.

AI is used strictly during the offline/learning phase to discover structural anchors
and column mappings. Runtime execution remains 100% deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import TYPE_CHECKING

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

    async def learn_from_workbook(
        self,
        workbook: Workbook,
        *,
        name: str = "learned_strategy",
    ) -> LearnedStrategy:
        """Analyze document sample via aip-provider AI to infer structural anchors and mappings."""
        ai = self._get_ai()
        sample_text = self._summarize_workbook_sample(workbook)

        system_prompt = (
            "You are an expert financial document layout analyzer. "
            "Analyze the provided sample rows from an unknown financial document and infer "
            "the canonical document type (one of: bank_statement, ledger, invoice, "
            "interest_certificate, tds_certificate), key structural anchor tokens, table headers, "
            "and column mapping. Return strictly valid JSON."
        )

        prompt = f"""Analyze this document sample:

{sample_text}

Respond ONLY with a JSON object with this schema:
{{
    "name": "{name}",
    "document_type": "bank_statement" | "ledger" | "invoice" | "interest_certificate" | "tds_certificate",
    "anchor_keywords": ["keyword1", "keyword2"],
    "table_header_keywords": ["header1", "header2"],
    "column_mapping": {{"standard_field": "header_in_document"}},
    "metadata_fields": {{"field_name": "label_in_document"}},
    "notes": "brief summary of detected layout"
}}
"""
        response = await ai.generate(prompt=prompt, system_prompt=system_prompt)
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
                "name": name,
                "document_type": "bank_statement",
                "notes": content[:100],
            }

        doc_type_val = data.get("document_type", "bank_statement").lower()
        try:
            doc_type = DocumentType(doc_type_val)
        except ValueError:
            doc_type = DocumentType.BANK_STATEMENT

        return LearnedStrategy(
            name=data.get("name", name),
            document_type=doc_type,
            anchor_keywords=list(data.get("anchor_keywords", [])),
            table_header_keywords=list(data.get("table_header_keywords", [])),
            column_mapping=dict(data.get("column_mapping", {})),
            metadata_fields=dict(data.get("metadata_fields", {})),
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
        # Find richer metadata that standard extractor could not capture
        additional_fields = [f for f in ai_fields if f not in baseline_fields]

        if len(additional_fields) > 0 or baseline_document is None:
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

    def generate_extractor_code(self, strategy: LearnedStrategy) -> str:
        """Synthesize Python extractor skeleton code based on learned strategy."""
        clean_name = "".join(part.capitalize() for part in strategy.name.split("_"))
        if not clean_name.endswith("Extractor"):
            clean_name += "Extractor"

        anchors_repr = repr(strategy.anchor_keywords)
        headers_repr = repr(strategy.table_header_keywords)
        col_map_repr = repr(strategy.column_mapping)
        meta_repr = repr(strategy.metadata_fields)

        return f'''from aip_canonica.extractors.base import Extractor
from aip_canonica.models import DocumentType, Workbook, CanonicalDocument

class {clean_name}:
    """Auto-synthesized extractor for '{strategy.name}' layout."""

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
        # Check if workbook contains structural anchors
        for sheet in workbook.sheets:
            for row in sheet.rows[:30]:
                row_text = " ".join(str(c.value).lower() for c in row.cells if c.value is not None)
                if any(a.lower() in row_text for a in anchors):
                    return True
        return False

    def extract(self, workbook: Workbook, *, source_name: str = "") -> CanonicalDocument:
        # Table headers: {headers_repr}
        # Column mappings: {col_map_repr}
        # Layout metadata: {meta_repr}
        # Implementation extracts transactions and bank metadata
        raise NotImplementedError("Implement custom extraction logic using discovered mappings")
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

        return f"""# Canonica AI Strategy Learning Report: {document_name}

- **Detected Document Type**: `{strategy.document_type.value}`
- **Recommendation**: `{recommendation.upper()}`
- **Candidate Strategy Name**: `{strategy.name}`
- **Generated Extractor File**: {extractor_link}

---

## 1. Discovered Structural Anchors & Table Headers
- **Anchor Keywords**: {", ".join(f"`{k}`" for k in strategy.anchor_keywords) or "None"}
- **Table Header Keywords**: {", ".join(f"`{k}`" for k in strategy.table_header_keywords) or "None"}

## 2. Discovered Column Mappings
| Canonical Field | Document Header / Label |
| :--- | :--- |
{col_rows or "| None | None |"}

## 3. Discovered Metadata Fields
| Field | Label / Source in Document |
| :--- | :--- |
{meta_rows or "| None | None |"}

## 4. Metadata Density Comparison
- **Standard Baseline Extracted Fields**: {", ".join(f"`{f}`" for f in baseline_fields) or "None"}
- **AI Discovered Metadata Fields**: {", ".join(f"`{f}`" for f in ai_fields) or "None"}
- **Richer Metadata Fields**: {", ".join(f"`{f}`" for f in additional_fields) or "None"}

## 5. Layout Observations
{strategy.notes or "No additional notes recorded."}

## 6. Generated Extractor Implementation Code
```python
{code_snippet or "# Generic fallback extractor is sufficient for this layout."}
```
"""
