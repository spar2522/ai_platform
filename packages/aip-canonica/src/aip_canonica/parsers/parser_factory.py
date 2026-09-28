from __future__ import annotations

from pathlib import Path

from .csv_parser import CsvParser
from .document_parser import DocumentParser
from .excel_parser import ExcelParser


class ParserFactory:

    @staticmethod
    def create(path: Path) -> DocumentParser:
        suffix = path.suffix.lower()

        if suffix in {".csv", ".tsv"}:
            return CsvParser()

        if suffix in {".xls", ".xlsx"}:
            return ExcelParser()

        raise ValueError(f"Unsupported document type: {suffix}")
