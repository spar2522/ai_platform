from aip_provider.base_provider import AIProvider
from aip_provider.config import AIProviderConfig
from aip_provider.factory import AIProviderFactory
from aip_provider.generation_options import GenerationOptions
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse
from aip_provider.provider_type import Provider


class AI:
    """
    Public entry point for the AI SDK.

    Examples
    --------
    
    # Local model with all defaults
    ai = AI.local()

    # Local model with overrides
    ai = AI.local(
        model="deepseek-r1:32b",
        generation=GenerationOptions(
            temperature=0.2,
        ),
    )

    # Generic constructor (useful for CLI/config)
    ai = AI(
        provider="local",
    )
    """

    def __init__(
        self,
        provider: str,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        generation: GenerationOptions | None = None,
    ) -> None:

        config = AIProviderConfig(
            provider=self._resolve_provider(provider),
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            generation=generation or GenerationOptions(),
        )

        self._provider: AIProvider = AIProviderFactory.create(config)

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        options: GenerationOptions | None = None,
    ) -> AIResponse:
        """
        Generate a response from the configured AI provider.
        """

        request = GenerationRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            options=options,
        )

        return await self._provider.generate(request)

    async def stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        options: GenerationOptions | None = None,
    ):
        """
        Stream a response from the configured AI provider.
        """

        request = GenerationRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            options=options,
        )

        async for chunk in self._provider.stream(request):
            yield chunk

    async def close(self):
        await self._provider.close()

    @classmethod
    def local(cls, **kwargs):
        return cls(
            provider="local",
            **kwargs,
        )

    @classmethod
    def gemini(cls, **kwargs):
        return cls(
            provider="gemini",
            **kwargs,
        )

    @classmethod
    def openai(cls, **kwargs):
        return cls(
            provider="openai",
            **kwargs,
        )

    @staticmethod
    def _resolve_provider(provider: str) -> Provider:

        providers = {
            "local": Provider.OLLAMA,
            "gemini": Provider.GEMINI,
            "openai": Provider.OPENAI,
            "dummy": Provider.DUMMY,
        }

        try:
            return providers[provider.lower()]
        except KeyError:
            supported = ", ".join(sorted(providers.keys()))
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Supported providers: {supported}"
            )