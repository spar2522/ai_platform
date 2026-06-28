from abc import ABC
from abc import abstractmethod


from ai_provider.config import GenerationConfig
from ai_provider.models import AIResponse


class AIProvider(ABC):
    """
    Base class for all AI providers. Defines the interface for interacting with
    language models, including generating complete responses and streaming tokens.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ) -> AIResponse:
        """
        Generate a complete response from a language model.

        Args:
            prompt: The input prompt to the model.
            options: Optional configuration for the generation process.

        Returns:
            AIResponse: The complete response from the model.
        """

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ):
        """
        Stream tokens from a language model incrementally.

        Args:
            prompt: The input prompt to the model.
            options: Optional configuration for the generation process.

        Returns:
            An asynchronous generator that yields tokens as they are produced.
        """