from pydantic import BaseModel, Field


class GenerationOptions(BaseModel):
    """Configuration options for AI generation processes.

    This class defines parameters that control the behavior of text generation
    in AI models, including temperature, output length, and stopping conditions.
    """

    temperature: float | None = Field(default=None, description="Controls the randomness of generated text. Higher values produce more diverse outputs.")
    stream: bool = Field(default=False, description="If True, returns output as a stream of tokens instead of waiting for completion.")
    max_tokens: int | None = Field(default=None, description="Maximum number of tokens to generate. If None, model-specific defaults apply.")
    top_p: float | None = Field(default=None, description="Controls the cumulative probability threshold for nucleus sampling.")
    seed: int | None = Field(default=None, description="Random seed for reproducible generation. If None, randomness is not controlled.")
    stop_sequences: list[str] | None = Field(default=None, description="List of sequences that, if generated, will stop the model from producing further tokens.")