from abc import ABC, abstractmethod
from pathlib import Path

from aip_canonica.models import Workbook


class DocumentParser(ABC):
    """
    Converts a physical document (e.g., CSV, Excel) into Canonica's internal workbook model.
    Subclasses must implement the parse method for specific file formats.
    """

    @abstractmethod
    def parse(
        self,
        path: Path,
    ) -> Workbook:
        """
        Parse a document from the specified file path.

        Parameters
        ----------
        path : Path
            Path to the document file. Must point to a valid file that can be processed
            by the implementing subclass (e.g., CSV, Excel).

        Returns
        -------
        Workbook
            A Canonica internal workbook model representing the parsed document.

        Raises
        ------
        FileNotFoundError
            If the specified path does not exist.
        ValueError
            If the file format is not supported by the implementing subclass.
        """