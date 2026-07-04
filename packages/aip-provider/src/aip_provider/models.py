from pydantic import BaseModel


class Usage(BaseModel):
    """Represents token usage statistics for an AI response."""

    prompt_tokens: int = 0  # Number of tokens in the prompt
    completion_tokens: int = 0  # Number of tokens in the completion
    total_tokens: int = 0  # Total number of tokens (prompt + completion)


class AIResponse(BaseModel):
    """Represents a response from an AI model."""

    text: str  # The content of the response
    model: str  # The name of the AI model used
    finish_reason: str | None = None  # Reason the response was finished
    usage: Usage | None = None  # Token usage statistics