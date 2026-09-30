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
    PARSER_MAP = {
        ".csv": CsvParser,
        ".tsv": CsvParser,
        ".xls": ExcelParser,
        ".xlsx": ExcelParser,
        ".pdf": PdfParser,
    }

    @staticmethod
    def create(path: Path, *, ai: AI | None = None) -> DocumentParser:
        """
        Create a DocumentParser instance based on the file's suffix.

        Args:
            path (Path): The file path to determine the parser for.
            ai (AI | None, optional): The AI instance to use for PDF parsing. Defaults to None.

        Returns:
            DocumentParser: An instance of the appropriate parser.

        Raises:
            ValueError: If the file type is not supported.
        """
        suffix = path.suffix.lower()
        parser_class = ParserFactory.PARSER_MAP.get(suffix)

        if parser_class is None:
            raise ValueError(f"Unsupported document type: {suffix}")

        if parser_class is PdfParser:
            return parser_class(ai=ai)

        return parser_class()