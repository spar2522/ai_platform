from __future__ import annotations

from typing import Any

from aip_provider.providers.defaults_ollama import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
)
import httpx

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_options import GenerationOptions
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse


class OllamaProvider(AIProvider):
    """
    Ollama implementation of AIProvider.

    This class is responsible only for translating our internal
    SDK models into Ollama's HTTP API.
    """

    DEFAULT_BASE_URL = "http://localhost:11443"

    def __init__(
        self,
        config: AIProviderConfig,
    ) -> None:
        """
        Initialize OllamaProvider.

        Args:
            config: Configuration object containing model and API settings.
        """
        self._config = config
        self._client = config.client or httpx.AsyncClient(base_url=self.DEFAULT_BASE_URL)

    def _init_defaults(self) -> None:
        """Initialize default configuration values."""
        self._model = self._config.model or DEFAULT_MODEL
        self._timeout = self._config.timeout or DEFAULT_TIMEOUT_SECONDS
        self._max_retries = self._config.max_retries or DEFAULT_MAX_RETRIES

    async def _resolve_generation_options(
        self, options: GenerationOptions
    ) -> GenerationOptions:
        """
        Merge generation options with defaults.

        Args:
            options: User-provided generation options.

        Returns:
            Merged generation options.
        """
        return options or GenerationOptions()

    async def _build_payload(
        self, options: GenerationOptions
    ) -> dict[str, Any]:
        """
        Construct request payload for Ollama API.

        Args:
            options: Generation options.

        Returns:
            Dictionary containing request payload.
        """
        payload = {
            "model": self._model,
            "stream": options.stream if hasattr(options, "stream") else False,
        }

        if options.temperature is not None:
            payload["temperature"] = options.temperature
        if options.top_p is not None:
            payload["top_p"] = options.top_p
        if options.seed is not None:
            payload["seed"] = options.seed
        if options.max_tokens is not None:
            payload["num_predict"] = options.max_tokens
        if options.stop_sequences:
            payload["stop"] = options.stop_sequences

        return payload

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        """
        Send POST request to Ollama API.

        Args:
            payload: Request payload.

        Returns:
            HTTP response from server.
        """
        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"API request failed: {e}") from e

    async def generate(
        self, request: GenerationRequest
    ) -> AIResponse:
        """
        Generate response from Ollama model.

        Args:
            request: Generation request containing prompt and options.

        Returns:
            AI response containing generated text and metadata.
        """
        options = await self._resolve_generation_options(request.options)
        payload = await self._build_payload(options)
        payload["prompt"] = request.prompt

        response = await self._post(payload)
        body = response.json()

        message = body.get("response", "")
        finish_reason = body.get("done_reason", "unknown")

        return AIResponse(
            text=message,
            model=self._model,
            finish_reason=finish_reason,
        )

    async def stream(
        self, request: GenerationRequest
    ) -> None:
        """
        Stream response from Ollama model.

        Note: Streaming functionality is not yet implemented.

        Args:
            request: Generation request containing prompt and options.

        Raises:
            NotImplementedError: Streaming is not currently supported.
        """
        raise NotImplementedError("Streaming support is not yet implemented.")