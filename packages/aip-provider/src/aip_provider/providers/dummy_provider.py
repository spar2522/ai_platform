from __future__ import annotations

from typing import AsyncIterator

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


class DummyProvider(AIProvider):
    """A dummy implementation of an AI provider for testing purposes."""

    def __init__(
        self,
        config: AIProviderConfig,
    ):
        pass

    async def generate(
        self,
        request: GenerationRequest,
    ) -> AIResponse:
        """Generates a dummy AI response."""
        return AIResponse(
            text="Dummy response",
            model="dummy",
        )

    async def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[AIResponse]:
        """Streams a dummy AI response."""
        yield AIResponse(
            text="Dummy",
            model="dummy",
        )
