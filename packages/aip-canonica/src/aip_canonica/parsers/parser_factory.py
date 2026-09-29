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
    """Factory class for creating document parsers based on file suffix."""

    @staticmethod
    def create(path: Path, *, ai: AI | None = None) -> DocumentParser:
        """Create a DocumentParser instance based on the file's suffix.

        Args:
            path: Path to the file.
            ai: Optional AI instance for PDF parsing.

        Returns:
            DocumentParser: The appropriate parser for the file type.

        Raises:
            ValueError: If the file type is not supported.
        """
        suffix = path.suffix.lower()

        if suffix in {".csv", ".tsv"}:
            return CsvParser()
        elif suffix in {".xls", ".xlsx"}:
            return ExcelParser()
        elif suffix == ".pdf":
            return PdfParser(ai=ai)
        else:
            raise ValueError(f"Unsupported document type: {suffix}")