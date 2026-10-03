from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .csv_parser import CsvParser
from .document_parser import DocumentParser
from .excel_parser import ExcelParser
from .pdf_parser import PdfParser

if TYPE_CHECKING:
    from aip_provider import AI


class ParserFactory:

    @staticmethod
    def create(path: Path, *, ai: AI | None = None) -> DocumentParser:
        suffix = path.suffix.lower()

        if suffix in {".csv", ".tsv"}:
            return CsvParser()

        if suffix in {".xls", ".xlsx"}:
            return ExcelParser()

        if suffix == ".pdf":
            return PdfParser(ai=ai)

        raise ValueError(f"Unsupported document type: {suffix}")
