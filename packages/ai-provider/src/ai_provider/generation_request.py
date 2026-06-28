from ai_provider.generation_options import GenerationOptions
from pydantic import BaseModel, ConfigDict


class GenerationRequest(BaseModel):
    """Represents a request for AI generation, containing the prompt, system instructions, and generation options."""

    model_config = ConfigDict(extra='forbid')

    prompt: str
    """The main input prompt for the AI to generate a response from."""

    system_prompt: str | None = None
    """Optional system-level instructions to guide the AI's behavior. Used for setting context or constraints."""

    options: GenerationOptions | None = None
    """Optional configuration parameters for controlling the generation process (e.g., temperature, max tokens)."""