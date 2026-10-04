from __future__ import annotations

from google import genai
from google.genai import types

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_options import GenerationOptions
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse, Usage

import logging
import os

logger = logging.getLogger("aip_provider.gemini")

DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash"


class GeminiProvider(AIProvider):
    """
    Gemini implementation of AIProvider.

    This class adapts our SDK models to Google's official SDK.
    """

    def __init__(
        self,
        config: AIProviderConfig,
    ) -> None:
        """
        Initialize the GeminiProvider with the given configuration.

        Args:
            config (AIProviderConfig): Configuration object containing API key, model, and generation options.

        Raises:
            ValueError: If no API key is provided in the configuration or environment variables.
        """
        api_key = config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini requires an API key. Pass api_key or set GEMINI_API_KEY / GOOGLE_API_KEY in the environment."
            )

        self._model = config.model or DEFAULT_MODEL
        self._generation_defaults = config.generation or GenerationOptions()

        self._client = genai.Client(
            api_key=api_key,
        )

    async def close(self) -> None:
        """Close the Gemini client connection."""
        await self._client.aio.aclose()

    def _resolve_generation_options(
        self,
        request: GenerationRequest,
    ) -> GenerationOptions:
        """
        Merge the request's generation options with the provider's default options.

        Args:
            request (GenerationRequest): The request containing user-specified options.

        Returns:
            GenerationOptions: Merged generation options.
        """
        return self._generation_defaults.model_copy(
            update=(
                request.options.model_dump(exclude_none=True) if request.options else {}
            )
        )

    def _build_config(
        self,
        request: GenerationRequest,
    ) -> types.GenerateContentConfig:
        """
        Construct the Google GenAI configuration from the request.

        Args:
            request (GenerationRequest): The request containing configuration parameters.

        Returns:
            types.GenerateContentConfig: Config object for the GenAI API.
        """
        options = self._resolve_generation_options(request)

        return types.GenerateContentConfig(
            system_instruction=request.system_prompt,
            temperature=options.temperature,
            max_output_tokens=options.max_tokens,
            top_p=options.top_p,
            stop_sequences=options.stop_sequences,
            seed=options.seed,
        )

    async def generate(
        self,
        request: GenerationRequest,
    ) -> AIResponse:
        """
        Generate a response using the Gemini model.

        Args:
            request (GenerationRequest): The request containing prompt and options.

        Returns:
            AIResponse: The generated response with metadata.

        Raises:
            Exception: If an unexpected error occurs during generation.
        """
        model_to_use = self._model
        config = self._build_config(request)

        try:
            response = await self._client.aio.models.generate_content(
                model=model_to_use,
                contents=request.prompt,
                config=config,
            )
        except Exception as exc:
            err_str = str(exc)
            if ("503" in err_str or "high demand" in err_str.lower()) and model_to_use != FALLBACK_MODEL:
                logger.warning(
                    f"Gemini model '{model_to_use}' experienced high demand (503). Gracefully falling back to '{FALLBACK_MODEL}'."
                )
                model_to_use = FALLBACK_MODEL
                response = await self._client.aio.models.generate_content(
                    model=model_to_use,
                    contents=request.prompt,
                    config=config,
                )
            else:
                raise

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
            usage = Usage(
                prompt_tokens=getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                completion_tokens=getattr(response.usage_metadata, "candidates_token_count", 0) or 0,
                total_tokens=getattr(response.usage_metadata, "total_token_count", 0) or 0,
            )

        return AIResponse(
            text=response.text or "",
            model=model_to_use,
            finish_reason=None,
            usage=usage,
        )

    async def stream(
        self,
        request: GenerationRequest,
    ):
        """
        Stream response generation (not yet implemented).

        Note: Streaming support is planned for a future release.

        Args:
            request (GenerationRequest): The request containing prompt and options.

        Yields:
            None: Placeholder implementation.
        """
        raise NotImplementedError("Streaming is not yet implemented for GeminiProvider.")