from ai_provider.provider_type import Provider
from pydantic import BaseModel
from pydantic import ConfigDict


class AIProviderConfig(BaseModel):

    model_config = ConfigDict(
        frozen=True,
    )

    provider: Provider

    model: str

    api_key: str | None = None

    base_url: str | None = None

    timeout_seconds: int = 120

    max_retries: int = 3

    stream: bool = False

    temperature: float = 0.7


class GenerationConfig(BaseModel):

    model: str | None = None

    stream: bool | None = None

    temperature: float | None = None
