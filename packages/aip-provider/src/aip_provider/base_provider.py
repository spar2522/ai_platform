from abc import ABC
from abc import abstractmethod


from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


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
