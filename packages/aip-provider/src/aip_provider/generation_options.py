from pydantic import BaseModel


class GenerationOptions(BaseModel):
    """Configuration options for text generation."""

    temperature: float | None = None
    """Controls the randomness of the generated text. Higher values produce more varied outputs."""

    stream: bool = False
    """Whether to stream the response as it is generated."""

    max_tokens: int | None = None
    """Maximum number of tokens to generate."""

    top_p: float | None = None
    """Cumulative probability for nucleus sampling."""

    seed: int | None = None
    """Seed value for reproducible generation."""

    stop_sequences: list[str] | None = None
    """List of sequences that, if generated, will stop the generation process."""