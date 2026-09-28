from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


class AIProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        request: GenerationRequest,
    ) -> AIResponse:
        """
        Generate a response from an LLM.
        """

    @abstractmethod
    def stream(
        self,
        request: GenerationRequest,
    ) -> AsyncIterator[Any]:
        """
        Stream tokens.
        """

    async def close(self) -> None:
        """Close provider resources."""
        pass
