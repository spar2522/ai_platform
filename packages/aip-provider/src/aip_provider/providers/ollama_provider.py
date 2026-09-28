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

    def __init__(
        self,
        config: AIProviderConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._init_defaults(config)

        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        )

    def _init_defaults(self, config: AIProviderConfig) -> None:
        self._model = config.model or DEFAULT_MODEL
        self._base_url = config.base_url or DEFAULT_BASE_URL
        self._timeout_seconds = config.timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        self._max_retries = config.max_retries or DEFAULT_MAX_RETRIES
        self._generation_defaults = config.generation or GenerationOptions()

    async def close(self) -> None:
        await self._client.aclose()

    def _resolve_generation_options(
        self,
        request: GenerationRequest,
    ) -> GenerationOptions:
        """
        Merge provider defaults with request overrides.

        Request values always win.
        """

        return self._generation_defaults.model_copy(
            update=(
                request.options.model_dump(exclude_none=True) if request.options else {}
            )
        )

    def _build_payload(
        self,
        request: GenerationRequest,
    ) -> dict[str, Any]:

        options = self._resolve_generation_options(request)

        messages: list[dict[str, str]] = []

        if request.system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": request.system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": request.prompt,
            }
        )

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": options.stream,
            "options": {},
        }

        if options.temperature is not None:
            payload["options"]["temperature"] = options.temperature

        if options.top_p is not None:
            payload["options"]["top_p"] = options.top_p

        if options.seed is not None:
            payload["options"]["seed"] = options.seed

        if options.max_tokens is not None:
            payload["options"]["num_predict"] = options.max_tokens

        if options.stop_sequences:
            payload["options"]["stop"] = options.stop_sequences

        if not payload["options"]:
            payload.pop("options")

        return payload

    async def _post(
        self,
        payload: dict[str, Any],
    ) -> httpx.Response:

        response = await self._client.post(
            "/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response

    async def _stream(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Stream response from Ollama.

        This method is not yet implemented. Streaming support will be added
        in a future release.
        """
        raise NotImplementedError("Streaming is not currently supported.")

    async def generate(
        self,
        payload: dict[str, Any],
    ) -> AIResponse:
        response = await self._post(payload)
        return AIResponse(
            content=response.json()["response"],
            finish_reason=response.json().get("done_reason"),
        )