import pytest

from aip_provider.base_provider import AIProvider
from aip_provider.provider_type import Provider


def test_aip_provider_is_abstract():
    """Verify that AIProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        AIProvider()


def test_aip_provider_enum_values():
    """Ensure that the Provider enum has the correct string value."""
    assert Provider.OLLAMA.value == "ollama"
