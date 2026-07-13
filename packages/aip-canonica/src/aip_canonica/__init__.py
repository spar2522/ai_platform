"""Package for Canonica AI Platform.

This package provides tools for configuring and understanding AI models.
"""

__version__ = "0.1.0"

from .api import understand
from .config import configure

__all__ = [
    "configure",
    "understand",
]