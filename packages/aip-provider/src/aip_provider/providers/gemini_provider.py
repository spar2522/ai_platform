from __future__ import annotations

from google import genai
from google.genai import types

from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.generation_options import GenerationOptions
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse

DEFAULT_MODEL = "gemini-2.5-flash"


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
            config: Configuration object containing API key, model, and generation options.

        Raises:
            ValueError: If the API key is not provided.
        """
        if config.api_key is None:
            raise ValueError("Gemini requires an API key.")

        self._model = config.model or DEFAULT_MODEL
        self._generation_defaults = config.generation or GenerationOptions()

        self._client = genai.Client(
            api_key=config.api_key,
        )

    async def close(self) -> None:
        """
        Close the client connection asynchronously.
        """
        await self._client.aio.aclose()

    def _resolve_generation_options(
        self,
        request: GenerationRequest,
    ) -> GenerationOptions:
        """
        Merge request-specific generation options with the default options.

        Args:
            request: The generation request containing optional parameters.

        Returns:
            Merged generation options.
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
        Construct the configuration object for the Gemini API.

        Args:
            request: The generation request containing prompt and system instructions.

        Returns:
            Configuration object for the Gemini API.
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
        Generate text based on the given request.

        Args:
            request: The generation request containing prompt and options.

        Returns:
            AIResponse object containing the generated text.
        """
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=request.prompt,
            config=self._build_config(request),
        )

        return AIResponse(
            text=response.text,
            model=self._model,
            finish_reason=None,
            usage=None,
        )

    async def stream(
        self,
        request: GenerationRequest,
    ):
        """
        Stream generation results (not implemented yet).

        Raises:
            NotImplementedError: Streaming is not currently supported.
        """
        raise NotImplementedError("Streaming support is coming in a future release.")