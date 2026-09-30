from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CanonicaConfig:
    """Global Canonica configuration.

    This class holds configuration parameters for the Canonica application.
    """

    learning_enabled: bool = True
    """Whether learning features are enabled in the application."""


_config = CanonicaConfig()


def configure(**kwargs: Any) -> None:
    """Update the global configuration with the provided keyword arguments.

    Args:
        **kwargs: Configuration parameters to set. Keys must correspond to attributes
            of the `CanonicaConfig` class.

    Raises:
        ValueError: If an invalid configuration key is provided.
    """
    global _config

    for key, value in kwargs.items():
        if not hasattr(_config, key):
            raise ValueError(f"Invalid configuration key: {key}")
        setattr(_config, key, value)


def get_config() -> CanonicaConfig:
    """Retrieve the current global configuration.

    Returns:
        CanonicaConfig: The current configuration instance.
    """
    return _config