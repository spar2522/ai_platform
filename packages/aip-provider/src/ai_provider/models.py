from pydantic import BaseModel


class Usage(BaseModel):

    prompt_tokens: int = 0

    completion_tokens: int = 0

    total_tokens: int = 0


class AIResponse(BaseModel):

    text: str

    model: str

    finish_reason: str | None = None

    usage: Usage | None = None
