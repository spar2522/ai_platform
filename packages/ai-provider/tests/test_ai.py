import pytest

from ai_provider import AI
from ai_provider import AIProviderConfig
from ai_provider.provider_type import Provider


@pytest.mark.asyncio
async def test_factory_returns_provider():

    provider = AI.create(
        AIProviderConfig(
            provider=Provider.OLLAMA,
            model="qwen3",
        )
    )

    response = await provider.generate("hello")

    assert response.text == "Dummy response"


def test_invalid_provider():

    class FakeProvider:

        value = "abc"

    with pytest.raises(ValueError):

        AI.create(
            AIProviderConfig(
                provider=FakeProvider(),
                model="x",
            )
        )
