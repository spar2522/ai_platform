from __future__ import annotations

from typing import AsyncIterator

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


class DummyProvider(AIProvider):
    """A dummy implementation of an AI provider for testing purposes.

    This provider ignores all input parameters and returns fixed responses.
    """

    def __init__(
        self,
        config: AIProviderConfig,
    ):
        """Initialize the dummy provider.

        Note: The config parameter is not used in this dummy implementation.
        """
        pass

    async def generate(
        self,
        request: GenerationRequest,
    ) -> AIResponse:
        """Generates a dummy AI response.

        Args:
            request (GenerationRequest): The generation request (ignored in this dummy implementation).

        Returns:
            AIResponse: A fixed response with "Dummy response" text and "dummy" model name.
        """
        return AIResponse(
            text="Dummy response",
            model="dummy",
        )

    async def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[AIResponse]:
        """Streams a dummy AI response.

        Args:
            request (GenerationRequest): The generation request (ignored in this dummy implementation).

        Yields:
            AIResponse: A fixed response with "Dummy" text and "dummy" model name.
        """
        yield AIResponse(
            text="Dummy",
            model="dummy",
        )