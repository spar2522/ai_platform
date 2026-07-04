from aip_provider.generation_options import GenerationOptions
from aip_provider.provider_type import Provider
from pydantic import BaseModel


class AIPProviderConfig(BaseModel):
    """Configuration class for the AIP provider."""

    provider: Provider
    """The provider type (e.g., OpenAI, Anthropic)."""

    model: str | None = None
    """The model name to use (e.g., 'gpt-4')."""

    api_key: str | None = None
    """API key for authentication."""

    base_url: str | None = None
    """Base URL for the API endpoint."""

    timeout_seconds: int | None = None
    """Timeout in seconds for API requests."""

    max_retries: int | None = None
    """Maximum number of retries for failed requests."""

    generation: GenerationOptions | None = None
    """Configuration options for text generation."""