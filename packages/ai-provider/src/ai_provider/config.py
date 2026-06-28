from ai_provider.generation_options import GenerationOptions
from ai_provider.provider_type import Provider
from pydantic import BaseModel


class AIProviderConfig(BaseModel):
    """Configuration for an AI provider.

    Attributes:
        provider: The type of AI provider to use.
        model: The model name to use for the AI provider.
        api_key: Optional API key for the provider (if required).
        base_url: Optional base URL for the provider's API.
        timeout_seconds: Timeout in seconds for API requests.
        max_retries: Maximum number of retries for failed requests.
        generation: Configuration options for text generation.
    """

    provider: Provider
    """The AI provider to use (e.g., OpenAI, Ollama)."""

    model: str
    """The model name to use for the AI provider."""

    api_key: str | None = None
    """Optional API key for the provider (if required)."""

    base_url: str | None = None
    """Optional base URL for the provider's API."""

    timeout_seconds: int = 120
    """Timeout in seconds for API requests."""

    max_retries: int = 3
    """Maximum number of retries for failed requests."""

    generation: GenerationOptions = GenerationOptions()
    """Configuration options for text generation (e.g., temperature, streaming)."""