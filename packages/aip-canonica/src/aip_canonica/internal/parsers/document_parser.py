from abc import ABC, abstractmethod
from pathlib import Path

from aip_canonica.internal.models import Workbook


class DocumentParser(ABC):
    """
    Converts a physical document into Canonica's internal workbook model.
    """

    @abstractmethod
    def parse(
        self,
        path: Path,
    ) -> Workbook:
        """
        Parse a document.

        Parameters
        ----------
        path:
            Path to the document.

        Returns
        -------
        Workbook
        """
