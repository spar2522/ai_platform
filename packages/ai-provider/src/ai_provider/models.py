from pydantic import BaseModel


class Usage(BaseModel):
    """Represents token usage statistics for an AI model response."""

    prompt_tokens: int = 0
    """Number of tokens in the prompt."""

    completion_tokens: int = 0
    """Number of tokens in the completion."""

    total_tokens: int = 0
    """Total number of tokens used (prompt + completion)."""


class AIResponse(BaseModel):
    """Represents a response from an AI model."""

    text: str
    """The content of the AI model's response."""

    model: str
    """The name or identifier of the AI model used."""

    finish_reason: str | None = None
    """The reason the model stopped generating text (e.g., 'stop', 'length')."""

    usage: Usage | None = None
    """Token usage statistics for this response."""