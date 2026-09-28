from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aip_canonica.storage.base import SourceStorage


@dataclass(slots=True)
class CanonicaConfig:
    """Global Canonica configuration.

    This class holds configuration parameters for the Canonica application.
    """

    learning_enabled: bool = True
    default_storage: SourceStorage | None = None

    def get_storage(self) -> SourceStorage:
        if self.default_storage is None:
            from aip_canonica.storage.providers import LocalReferenceStorage

            self.default_storage = LocalReferenceStorage()
        return self.default_storage


_config = CanonicaConfig()


def configure(**kwargs):
    """Update the global configuration with the provided keyword arguments.

    Args:
        **kwargs: Configuration parameters to set.
    """
    global _config

    for key, value in kwargs.items():
        setattr(_config, key, value)


def get_config() -> CanonicaConfig:
    """Retrieve the current global configuration.

    Returns:
        CanonicaConfig: The current configuration instance.
    """
    return _config