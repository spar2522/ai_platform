from ai_provider.base_provider import AIProvider
from ai_provider.config import GenerationConfig
from ai_provider.models import AIResponse


class DummyProvider(AIProvider):

    async def generate(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ) -> AIResponse:

        return AIResponse(
            text="Dummy response",
            model="dummy",
        )

    async def stream(
        self,
        prompt: str,
        options: GenerationConfig | None = None,
    ):
        yield AIResponse(
            text="Dummy",
            model="dummy",
        )
