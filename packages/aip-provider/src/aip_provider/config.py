from aip_provider.generation_options import GenerationOptions
from aip_provider.provider_type import Provider
from pydantic import BaseModel


class AIProviderConfig(BaseModel):

    provider: Provider

    model: str | None = None

    api_key: str | None = None

    base_url: str | None = None

    timeout_seconds: int | None = None

    max_retries: int | None = None

    generation: GenerationOptions | None = None
