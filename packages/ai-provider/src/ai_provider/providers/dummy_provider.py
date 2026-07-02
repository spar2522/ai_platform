from ai_provider.base_provider import AIProvider
from ai_provider.config import AIProviderConfig
from ai_provider.generation_options import GenerationOptions
from ai_provider.models import AIResponse


class DummyProvider(AIProvider):
    """A dummy implementation of an AI provider for testing purposes."""

    def __init__(
        self,
        config: AIProviderConfig,
    ):
        """Initialize the dummy provider with configuration.

        Note: The configuration is not used in this dummy implementation.
        """
        pass

    async def generate(
        self,
        prompt: str,
        options: GenerationOptions | None = None,
    ) -> AIResponse:
        """Generates a dummy AI response.

        Args:
            prompt (str): The input prompt (not used in this dummy implementation).
            options (GenerationOptions | None): Generation options (not used in this dummy implementation).

        Returns:
            AIResponse: A dummy response with fixed text and model name.
        """
        return AIResponse(
            text="Dummy response",
            model="dummy",
        )

    async def stream(
        self,
        prompt: str,
        options: GenerationOptions | None = None,
    ):
        """Streams a dummy AI response.

        Args:
            prompt (str): The input prompt (not used in this dummy implementation).
            options (GenerationOptions | None): Generation options (not used in this dummy implementation).

        Yields:
            AIResponse: A dummy response with fixed text and model name.
        """
        yield AIResponse(
            text="Dummy",
            model="dummy",
        )