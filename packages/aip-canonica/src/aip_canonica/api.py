from pathlib import Path

from .internal.parsers import ParserFactory


def understand(path: str | Path):

    parser = ParserFactory.create(Path(path))

    workbook = parser.parse(Path(path))

    return workbook
