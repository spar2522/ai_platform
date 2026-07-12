from pathlib import Path

from aip_canonica.internal.models import Workbook

from .document_parser import DocumentParser


class ExcelParser(DocumentParser):

    def parse(
        self,
        path: Path,
    ) -> Workbook:
        raise NotImplementedError()
