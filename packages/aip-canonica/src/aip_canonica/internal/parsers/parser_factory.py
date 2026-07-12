from pathlib import Path

from .csv_parser import CsvParser
from .excel_parser import ExcelParser
from .document_parser import DocumentParser


class ParserFactory:

    @staticmethod
    def create(path: Path) -> DocumentParser:

        suffix = path.suffix.lower()

        if suffix == ".csv":
            return CsvParser()

        if suffix in {".xls", ".xlsx"}:
            return ExcelParser()

        raise ValueError(f"Unsupported document type: {suffix}")
