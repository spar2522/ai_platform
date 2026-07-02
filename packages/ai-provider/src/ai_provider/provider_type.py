from enum import StrEnum


class Provider(StrEnum):
    """Enum representing different AI service providers.

    This enum lists all supported AI service providers. Each member corresponds
    to a specific AI service, with the exception of DUMMY, which is used for
    testing and development purposes.
    """

    ANTHROPIC = "anthropic"
    """Anthropic AI service provider."""

    DUMMY = "dummy"
    """Dummy provider for testing and development purposes."""

    GEMINI = "gemini"

    OLLAMA = "ollama"

    OPENAI = "openai"
    """OpenAI service provider."""