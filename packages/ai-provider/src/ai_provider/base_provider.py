from abc import ABC
from abc import abstractmethod


from ai_provider.generation_request import GenerationRequest
from ai_provider.models import AIResponse


class AIProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        request: GenerationRequest | None = None,
    ) -> AIResponse:
        """
        Generate a response from an LLM.
        """

    @abstractmethod
    async def stream(
        self,
        request: GenerationRequest | None = None,
    ):
        """
        Stream tokens.
        """
