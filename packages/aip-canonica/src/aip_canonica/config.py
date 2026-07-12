from dataclasses import dataclass


@dataclass(slots=True)
class CanonicaConfig:
    """
    Global Canonica configuration.
    """

    learning_enabled: bool = True


_config = CanonicaConfig()


def configure(**kwargs):
    global _config

    for key, value in kwargs.items():
        setattr(_config, key, value)


def get_config() -> CanonicaConfig:
    return _config
