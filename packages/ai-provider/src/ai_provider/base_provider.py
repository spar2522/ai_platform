from abc import ABC
from abc import abstractmethod


from ai_provider.config import GenerationConfig
from ai_provider.models import AIResponse


class AIProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ) -> AIResponse:
        """
        Generate a response from an LLM.
        """

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ):
        """
        Stream tokens.
        """
