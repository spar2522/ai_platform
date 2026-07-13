from dataclasses import dataclass


@dataclass(slots=True)
class CanonicaConfig:
    """
    Global Canonica configuration.

    This class holds configuration parameters for the Canonica application.
    """
    learning_enabled: bool = True


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