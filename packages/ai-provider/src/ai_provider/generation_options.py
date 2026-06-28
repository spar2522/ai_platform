from pydantic import BaseModel


class GenerationOptions(BaseModel):

    temperature: float | None = None

    stream: bool = False

    max_tokens: int | None = None

    top_p: float | None = None

    seed: int | None = None

    stop_sequences: list[str] | None = None
