from ai_provider.generation_options import GenerationOptions
from ai_provider.provider_type import Provider
from pydantic import BaseModel


class AIProviderConfig(BaseModel):

    provider: Provider

    model: str

    api_key: str | None = None

    base_url: str | None = None

    timeout_seconds: int = 120

    max_retries: int = 3

    generation: GenerationOptions = GenerationOptions()
