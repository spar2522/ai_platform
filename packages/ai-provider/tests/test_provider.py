import pytest

from ai_provider.base_provider import AIProvider
from ai_provider.provider_type import Provider


def test_provider_is_abstract():

    with pytest.raises(TypeError):

        AIProvider()


def test_provider_enum():

    assert Provider.OLLAMA.value == "ollama"
