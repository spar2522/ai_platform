"""Default configuration values for the Ollama provider."""

DEFAULT_MODEL: str = "qwen3:14b"
"""Default model to use for Ollama requests."""

DEFAULT_BASE_URL: str = "http://localhost:11434"
"""Default base URL for the Ollama server."""

DEFAULT_TIMEOUT_SECONDS: int = 120
"""Default timeout in seconds for Ollama requests."""

DEFAULT_MAX_RETRIES: int = 3
"""Default maximum number of retry attempts for Ollama requests."""