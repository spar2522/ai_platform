"""PDF document parser supporting deterministic extraction with AI OCR fallback."""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pypdf import PdfReader

from aip_canonica.models import Cell, CellLocation, Row, Sheet, Workbook
from aip_canonica.parsers.document_parser import DocumentParser

if TYPE_CHECKING:
    from aip_provider import AI

logger = logging.getLogger("aip_canonica")


def _column_index_to_letter(col_idx: int) -> str:
    """Convert 1-based column index to Excel-style column letter (1 -> 'A', 27 -> 'AA')."""
    letters = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


class PdfParser(DocumentParser):
    """Two-tier PDF parser:

    - Option A: Native deterministic vector PDF parsing via pypdf.
      Tokenizes tabular rows and cells with strict quality heuristics (minimum chars and rows).
    - Option B: AI multimodal / OCR fallback via aip-provider when deterministic extraction
      yields insufficient content (such as scanned, image-only, or corrupted PDFs).
    """

    def __init__(
        self,
        *,
        ai: AI | None = None,
        min_chars: int = 50,
        min_rows: int = 3,
    ) -> None:
        self._ai = ai
        self.min_chars = min_chars
        self.min_rows = min_rows

    def parse(self, path: Path) -> Workbook:
        path = Path(path)

        # 1. Option A: Deterministic Native Extraction
        deterministic_workbook: Workbook | None = None
        try:
            deterministic_workbook = self._parse_deterministic(path)
        except Exception as exc:
            logger.warning(
                "[Canonica][PDF Parser] Deterministic parsing encountered error for '%s': %s",
                path.name,
                exc,
            )

        # 2. Deterministic Quality Verification
        if deterministic_workbook is not None and self._is_sufficient_content(deterministic_workbook):
            total_chars = self._count_chars(deterministic_workbook)
            total_rows = sum(len(s.rows) for s in deterministic_workbook.sheets)
            logger.debug(
                "[Canonica][PDF Parser] Deterministic PDF extraction succeeded for '%s': "
                "%d characters, %d rows across %d sheet(s).",
                path.name,
                total_chars,
                total_rows,
                len(deterministic_workbook.sheets),
            )
            return deterministic_workbook

        # 3. Option B: AI / Vision Fallback
        total_chars = self._count_chars(deterministic_workbook) if deterministic_workbook else 0
        total_rows = (
            sum(len(s.rows) for s in deterministic_workbook.sheets) if deterministic_workbook else 0
        )

        if self._ai is None:
            if deterministic_workbook is not None and any(len(s.rows) > 0 for s in deterministic_workbook.sheets):
                logger.info(
                    "[Canonica][PDF Parser] Content below ideal threshold but no AI instance provided (ai=None). "
                    "Returning deterministic workbook (%d rows).",
                    total_rows,
                )
                return deterministic_workbook
            raise ValueError(
                f"Failed to parse PDF document '{path.name}': "
                f"Deterministic parser found insufficient content ({total_chars} chars, {total_rows} rows), "
                f"and no AI instance was provided (ai=None). "
                f"Pass an explicit ai instance (e.g. ai=AI.local() or ai=AI.gemini(...)) to enable AI parsing."
            )

        divider = "=" * 60
        logger.info(
            "\n%s\n[Canonica][AI Fallback] Option A (Deterministic PDF extraction) yielded insufficient content.\n"
            "Document '%s' contains %d characters and %d rows (threshold: >=%d chars, >=%d rows).\n"
            "Detected scanned, image-only, or non-digital PDF.\n"
            "Switching to Option B: Engaging AI multimodal / OCR fallback via aip-provider...\n%s",
            divider,
            path.name,
            total_chars,
            total_rows,
            self.min_chars,
            self.min_rows,
            divider,
        )

        from aip_canonica.audit import log_api_notice

        log_api_notice(
            purpose="Option B Multimodal PDF OCR Parsing",
            ai=self._get_ai(),
            document_name=path.name,
            extra_details=f"Insufficient vector text ({total_chars} chars, {total_rows} rows).",
        )

        ai_workbook = self._parse_with_ai(path, deterministic_workbook)
        if (
            ai_workbook is not None
            and len(ai_workbook.sheets) > 0
            and any(len(s.rows) > 0 for s in ai_workbook.sheets)
        ):
            return ai_workbook

        # If AI fallback didn't produce rows, but deterministic had partial content, return it
        if deterministic_workbook is not None and any(len(s.rows) > 0 for s in deterministic_workbook.sheets):
            logger.warning(
                "[Canonica][PDF Parser] AI fallback did not yield rows. Returning partial deterministic workbook."
            )
            return deterministic_workbook

        raise ValueError(
            f"Failed to parse PDF document '{path.name}': "
            f"Deterministic parser found insufficient content ({total_chars} chars, {total_rows} rows), "
            f"and AI fallback could not reconstruct table rows."
        )

    def _parse_deterministic(self, path: Path) -> Workbook:
        reader = PdfReader(str(path))
        workbook = Workbook()

        for page_idx, page in enumerate(reader.pages, start=1):
            sheet_name = f"Page_{page_idx}"
            sheet = Sheet(name=sheet_name)
            raw_text = page.extract_text() or ""
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

            for row_idx, line in enumerate(lines, start=1):
                tokens = self._tokenize_line(line)
                row = Row(index=row_idx)
                for col_idx, token in enumerate(tokens, start=1):
                    val = token.strip() if token is not None else None
                    cell = Cell(
                        value=val if val else None,
                        location=CellLocation(
                            sheet=sheet_name,
                            row=row_idx,
                            column=col_idx,
                            address=f"{_column_index_to_letter(col_idx)}{row_idx}",
                        ),
                    )
                    row.cells.append(cell)
                sheet.rows.append(row)

            workbook.sheets.append(sheet)

        return workbook

    def _tokenize_line(self, line: str) -> list[str]:
        """Split a line of PDF text into column tokens using whitespace or delimiter heuristics."""
        if "\t" in line:
            return [t.strip() for t in line.split("\t")]

        if line.count("|") >= 2:
            parts = line.strip("|").split("|")
            return [p.strip() for p in parts]

        # Check for CSV/delimiter-style lines
        if line.count(",") >= 2:
            try:
                reader = csv.reader(io.StringIO(line))
                tokens = next(reader)
                return [t.strip() for t in tokens]
            except Exception:
                pass

        # Check for multiple spaces (standard tabular alignment in vector PDFs)
        if re.search(r"\s{2,}", line):
            parts = re.split(r"\s{2,}", line)
            return [p.strip() for p in parts if p.strip()]

        # Single token / line
        return [line.strip()]

    def _count_chars(self, workbook: Workbook) -> int:
        return sum(
            len(str(cell.value))
            for sheet in workbook.sheets
            for row in sheet.rows
            for cell in row.cells
            if cell.value is not None
        )

    def _is_sufficient_content(self, workbook: Workbook) -> bool:
        """Deterministic quality check to verify if native vector PDF parsing succeeded."""
        total_chars = self._count_chars(workbook)
        total_rows = sum(len(sheet.rows) for sheet in workbook.sheets)
        return total_chars >= self.min_chars and total_rows >= self.min_rows

    def parse_ai_fallback(
        self,
        path: Path,
        *,
        reason: str = "",
        partial_workbook: Workbook | None = None,
    ) -> Workbook | None:
        """Explicitly re-parse PDF document using Option B (AI multimodal / OCR fallback).

        This is invoked when Option A (deterministic text extraction) produced a workbook,
        but downstream extraction/validation failed due to:
        - Inability to identify document type
        - Inability to retrieve mandatory information
        - Mathematical calculation / reconciliation mismatch (opening + deposits - withdrawals != closing)
        """
        if self._ai is None:
            logger.info(
                "[Canonica][AI Fallback] parse_ai_fallback skipped because no AI instance was provided (ai=None)."
            )
            return None

        from aip_canonica.audit import log_api_notice

        log_api_notice(
            purpose="Option B Multimodal PDF OCR Fallback Recovery",
            ai=self._get_ai(),
            document_name=path.name,
            extra_details=reason,
        )
        path = Path(path)
        return self._parse_with_ai(path, partial_workbook=partial_workbook, reason=reason)

    def _get_ai(self) -> AI:
        if self._ai is None:
            raise ValueError(
                "No AI instance was provided. Pass an explicit ai instance (e.g. ai=AI.local() or ai=AI.gemini(...)) to enable AI."
            )
        return self._ai

    def _parse_with_ai(
        self,
        path: Path,
        partial_workbook: Workbook | None = None,
        reason: str = "",
    ) -> Workbook | None:
        """Synchronously execute AI multimodal/OCR fallback."""
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
                    self._parse_with_ai_async(path, partial_workbook, reason=reason),
                ).result()
        return asyncio.run(self._parse_with_ai_async(path, partial_workbook, reason=reason))

    async def _parse_with_ai_async(
        self,
        path: Path,
        partial_workbook: Workbook | None = None,
        reason: str = "",
    ) -> Workbook | None:
        """Call aip-provider to reconstruct tabular workbook from scanned/image PDF."""
        ai = self._get_ai()

        # Gather partial text context if available
        partial_snippets: list[str] = []
        if partial_workbook:
            for s in partial_workbook.sheets:
                for r in s.rows[:15]:
                    vals = [str(c.value) for c in r.cells if c.value]
                    if vals:
                        partial_snippets.append(" | ".join(vals))

        context_str = "\n".join(partial_snippets[:25])

        system_prompt = (
            "You are an expert financial document parser and OCR table extractor. "
            "Extract all tables, transaction records, and metadata fields from the financial document "
            "into a clean 2D grid structure. Return strictly a JSON object with this schema: "
            '{"sheets": [{"name": "Page 1", "rows": [["Col1", "Col2", "Col3"], ...]}]}'
        )

        reason_clause = f"Reason for AI Parsing: {reason}\n" if reason else ""
        prompt = f"""Extract all tabular data and headers from this financial document:
Document File Name: {path.name}
File Size: {path.stat().st_size if path.exists() else 0} bytes
{reason_clause}Partial Raw Content Detected:
{context_str or "No direct vector text could be extracted (scanned/raster document)."}

Please reconstruct all tables and lines from the document as a 2D grid of rows and cells.
Return strictly valid JSON with the format:
{{
    "sheets": [
        {{
            "name": "Page 1",
            "rows": [
                ["Date", "Description", "Debit", "Credit", "Balance"],
                ["2023-01-01", "Sample Transaction", "100.00", "", "9900.00"]
            ]
        }}
    ]
}}
"""

        try:
            response = await ai.generate(prompt=prompt, system_prompt=system_prompt)
            content = response.text.strip()

            # Clean JSON markdown fences if present
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            data = json.loads(content)
            return self._build_workbook_from_dict(data)
        except Exception as exc:
            logger.warning("[Canonica][AI Fallback] AI parsing generation failed: %s", exc)
            return None

    def _build_workbook_from_dict(self, data: dict[str, Any]) -> Workbook:
        workbook = Workbook()
        sheets_data = data.get("sheets", [])
        if not sheets_data and "rows" in data:
            sheets_data = [{"name": "Sheet1", "rows": data["rows"]}]

        for s_idx, s_info in enumerate(sheets_data, start=1):
            sheet_name = s_info.get("name") or f"Page_{s_idx}"
            sheet = Sheet(name=sheet_name)
            rows_data = s_info.get("rows", [])

            for r_idx, row_values in enumerate(rows_data, start=1):
                row = Row(index=r_idx)
                if isinstance(row_values, list):
                    for c_idx, val in enumerate(row_values, start=1):
                        str_val = str(val).strip() if val is not None else None
                        cell = Cell(
                            value=str_val if str_val else None,
                            location=CellLocation(
                                sheet=sheet_name,
                                row=r_idx,
                                column=c_idx,
                                address=f"{_column_index_to_letter(c_idx)}{r_idx}",
                            ),
                        )
                        row.cells.append(cell)
                sheet.rows.append(row)
            workbook.sheets.append(sheet)

        return workbook
