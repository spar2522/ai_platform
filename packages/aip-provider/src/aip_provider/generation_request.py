from aip_provider.generation_options import GenerationOptions
from pydantic import BaseModel


class GenerationRequest(BaseModel):
    """Represents a request for text generation, including prompt, system instructions, and generation options."""

    prompt: str
    """The main input text prompt for the generation task."""

    system_prompt: str | None = None
    """Optional system-level instructions or context to guide the generation process."""

    options: GenerationOptions | None = None
    """Optional configuration parameters for controlling the generation behavior."""