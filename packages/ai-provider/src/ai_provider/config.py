from ai_provider.provider_type import Provider
from pydantic import BaseModel
from pydantic import ConfigDict


class AIProviderConfig(BaseModel):
    """
    Configuration for an AI provider.

    This class holds the necessary parameters to configure an AI provider,
    including required fields like provider and model, and optional fields
    such as API key and base URL.
    """

    model_config = ConfigDict(
        frozen=True,
    )
    """Configuration for the model, set to frozen to prevent modification after creation."""

    provider: Provider
    """The AI provider to use (e.g., OpenAI, Anthropic)."""

    model: str
    """The model name to use for the provider (e.g., 'gpt-4', 'claude-3')."""

    api_key: str | None = None
    """API key for authentication with the provider. Can be None if not required."""

    base_url: str | None = None
    """Base URL for the provider's API. Can be None if using the default endpoint."""

    timeout_seconds: int = 120
    """Maximum time in seconds to wait for a response from the provider."""

    max_retries: int = 3
    """Number of retry attempts for failed requests."""

    stream: bool = False
    """Whether to stream responses from the provider."""

    temperature: float = 0.7
    """Temperature parameter for controlling randomness in text generation."""


class GenerationConfig(BaseModel):
    """
    Configuration for a single AI generation request.

    This class holds optional parameters that can be used to customize a
    specific generation request, such as model, stream, and temperature.
    """

    model: str | None = None
    """Model to use for this generation. If None, uses the provider's default model."""

    stream: bool | None = None
    """Whether to stream the response for this generation. If None, uses the provider's default."""

    temperature: float | None = None
    """Temperature parameter for this generation. If None, uses the provider's default temperature."""