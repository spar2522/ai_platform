import pytest

from ai_provider import AI
from ai_provider import AIProviderConfig
from ai_provider.provider_type import Provider


@pytest.mark.asyncio
async def test_ai_factory_returns_correct_provider_for_ollama():
    """
    Test that AI factory returns the correct provider instance when OLLAMA is specified.
    """
    # Create AI instance with OLLAMA provider and specific model
    provider = AI.create(
        AIProviderConfig(
            provider=Provider.OLLAMA,
            model="qwen3",
        )
    )

    # Generate response and verify the expected dummy output
    response = await provider.generate("hello")
    assert response.text == "Dummy response"


def test_ai_factory_raises_error_for_invalid_provider():
    """
    Test that AI factory raises ValueError when an invalid provider is specified.
    """
    # Define a fake provider class that does not implement required interface
    class FakeProvider:
        value = "abc"

    # Verify that using invalid provider raises appropriate error
    with pytest.raises(ValueError):
        AI.create(
            AIProviderConfig(
                provider=FakeProvider(),
                model="x",
            )
        )