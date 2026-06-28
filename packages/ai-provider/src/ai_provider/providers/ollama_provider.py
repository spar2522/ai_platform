from __future__ import annotations

from typing import Any

import httpx

from ai_provider.base_provider import AIProvider
from ai_provider.config import AIProviderConfig
from ai_provider.generation_options import GenerationOptions
from ai_provider.generation_request import GenerationRequest
from ai_provider.models import AIResponse


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
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Initialize the OllamaProvider.

        Args:
            config: Configuration for the AI provider.
            client: Optional httpx.AsyncClient to use for HTTP requests.
        """
        self._config = config
        self._client = client or httpx.AsyncClient(
            base_url=config.base_url or self.DEFAULT_BASE_URL,
            timeout=config.timeout_seconds,
        )

    async def close(self) -> None:
        """
        Close the HTTP client.
        """
        await self._client.aclose()

    def _resolve_generation_options(self, options: GenerationOptions) -> GenerationOptions:
        """
        Merge the default generation options with the request's options.

        Request values always take precedence over default values.

        Args:
            options: The generation options from the request.

        Returns:
            Merged generation options.
        """
        return self._config.generation_options.model_copy(update=options.model_dump())

    def _build_payload(self, options: GenerationOptions) -> dict[str, Any]:
        """
        Build the payload for the Ollama API request.

        Args:
            options: The generation options.

        Returns:
            Dictionary containing the payload for the request.
        """
        payload = {
            "model": self._config.model,
            "messages": [],
        }

        # Add system message if present
        if self._config.system_prompt:
            payload["messages"].append({"role": "system", "content": self._config.system_prompt})

        # Add user message
        payload["messages"].append({"role": "user", "content": options.prompt})

        # Map generation options to Ollama API parameters
        ollama_option_mapping = {
            "temperature": "temperature",
            "top_p": "top_p",
            "seed": "seed",
            "max_tokens": "num_predict",
            "stop_sequences": "stop",
        }

        payload["options"] = {}
        for attr, key in ollama_option_mapping.items():
            value = getattr(options, attr)
            if value is not None:
                payload["options"][key] = value

        # If no options are set, remove the key
        if not payload["options"]:
            del payload["options"]

        return payload

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send a POST request to the Ollama API.

        Args:
            payload: The request payload.

        Returns:
            Dictionary containing the response data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        return response.json()

    async def generate(self, options: GenerationOptions) -> AIResponse:
        """
        Generate a response from the Ollama API.

        Args:
            options: The generation options.

        Returns:
            AIResponse object containing the generated response.
        """
        payload = self._build_payload(options)
        response_data = await self._post(payload)

        # Extract response content
        content = response_data.get("response", "")
        finish_reason = response_data.get("done_reason", "unknown")

        return AIResponse(content=content, finish_reason=finish_reason)

    async def stream(self, options: GenerationOptions) -> None:
        """
        Stream responses from the Ollama API.

        This method is not yet implemented.

        Args:
            options: The generation options.
        """
        raise NotImplementedError("Streaming is not yet implemented.")