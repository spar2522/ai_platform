from enum import StrEnum


class Provider(StrEnum):
    """Enum representing different AI service providers."""

    OLLAMA = "ollama"

    GEMINI = "gemini"

    OPENAI = "openai"

    ANTHROPIC = "anthropic"

    DUMMY = "dummy"
