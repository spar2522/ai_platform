from ai_provider.config import AIProviderConfig


def test_defaults():

    config = AIProviderConfig(
        provider="ollama",
        model="qwen3",
    )

    assert config.timeout_seconds == 120
    assert config.stream is False
    assert config.max_retries == 3
