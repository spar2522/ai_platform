from ai_provider.generation_options import GenerationOptions
from ai_provider.provider_type import Provider
from pydantic import BaseModel, Field

class AIProviderConfig(BaseModel):
    model_config = ConfigDict(extra='ignore')

    provider: Provider = Field(..., description="The AI provider to use (e.g., 'openai', 'anthropic').")

    model: str | None = Field(None, description="The model to use for the AI provider (e.g., 'gpt-4', 'claude-3').")

    api_key: str | None = Field(None, description="The API key for the AI provider.")

    base_url: str | None = Field(None, description="The base URL for the AI provider's API.")

    timeout_seconds: int | None = Field(None, description="The timeout in seconds for API requests.")

    max_retries: int | None = Field(None, description="The maximum number of retries for failed requests.")

    generation: GenerationOptions | None = Field(None, description="Additional generation options for the AI provider.")