from __future__ import annotations

from typing import AsyncIterator

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


class DummyProvider(AIProvider):
    """A dummy implementation of an AI provider for testing purposes.

    This provider returns fixed responses regardless of input and is intended for
    validation and testing of the provider framework.
    """

    def __init__(
        self,
        config: AIProviderConfig,
    ):
        """Initialize the dummy provider with the given configuration.

        Args:
            config (AIProviderConfig): Configuration for the provider (not used in this dummy implementation).
        """
        super().__init__(config)

    async def generate(
        self,
        request: GenerationRequest,
    ) -> AIResponse:
        """Generates a dummy AI response.

        Args:
            request (GenerationRequest): The generation request (not used in this dummy implementation).

        Returns:
            AIResponse: A dummy response with fixed text and model name.
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
            request (GenerationRequest): The generation request (not used in this dummy implementation).

        Yields:
            AIResponse: A dummy response with fixed text and model name.
        """
        yield AIResponse(
            text="Dummy",
            model="dummy",
        )