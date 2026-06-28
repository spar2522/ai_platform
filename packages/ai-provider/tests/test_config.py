from ai_provider.config import AIProviderConfig


def test_defaults():
    """Test that default configuration values are set correctly when provider and model are specified."""
    config = AIProviderConfig(
        provider="ollama",
        model="qwen3",
    )

    assert config.timeout_seconds == 120
    assert config.stream is False
    assert config.max_retries == 3