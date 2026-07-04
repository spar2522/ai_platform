from enum import StrEnum


class Provider(StrEnum):
    """Enum representing different AIP service providers."""

    OLLAMA = "ollama"

    GEMINI = "gemini"

    OPENAI = "openai"

    ANTHROPIC = "anthropic"

    DUMMY = "dummy"