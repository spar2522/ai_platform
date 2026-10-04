from unittest.mock import AsyncMock, MagicMock
import pytest

from aip_provider.config import AIProviderConfig
from aip_provider.generation_request import GenerationRequest
from aip_provider.provider_type import Provider
from aip_provider.providers.gemini_provider import DEFAULT_MODEL, FALLBACK_MODEL, GeminiProvider


def test_gemini_provider_init_with_explicit_key():
    # Test that provider initializes correctly with an explicitly provided API key
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="explicit-test-key",
    )
    provider = GeminiProvider(config)
    assert provider._model == DEFAULT_MODEL


def test_gemini_provider_init_with_env_key(monkeypatch):
    # Test that provider initializes correctly when API key is set in the environment
    monkeypatch.setenv("GEMINI_API_KEY", "env-test-key")
    config = AIProviderConfig(
        provider=Provider.GEMINI,
    )
    provider = GeminiProvider(config)
    assert provider._model == DEFAULT_MODEL


def test_gemini_provider_init_without_key_raises(monkeypatch):
    # Test that provider raises an error when no API key is provided
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    config = AIProviderConfig(
        provider=Provider.GEMINI,
    )
    with pytest.raises(ValueError, match="Gemini requires an API key"):
        GeminiProvider(config)


@pytest.mark.asyncio
async def test_gemini_provider_generate_with_usage():
    # Test that token usage is correctly tracked during generation
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    mock_resp = MagicMock()
    mock_resp.text = "Hello world"
    mock_resp.usage_metadata = MagicMock()
    mock_resp.usage_metadata.prompt_token_count = 15
    mock_resp.usage_metadata.candidates_token_count = 8
    mock_resp.usage_metadata.total_token_count = 23

    provider._generate = AsyncMock(return_value=mock_resp)

    result = await provider.generate(GenerationRequest(prompt="test"))
    assert result.text == "Hello world"
    assert result.usage.prompt_tokens == 15
    assert result.usage.completion_tokens == 8
    assert result.usage.total_tokens == 23


@pytest.mark.asyncio
async def test_gemini_provider_fallback_on_503():
    # Test that provider falls back to a secondary model on 503 error
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    mock_resp_first = MagicMock()
    mock_resp_first.status_code = 503
    mock_resp_first.text = "Service unavailable"

    mock_resp_second = MagicMock()
    mock_resp_second.text = "Fallback response"
    mock_resp_second.usage_metadata = MagicMock()
    mock_resp_second.usage_metadata.prompt_token_count = 10
    mock_resp_second.usage_metadata.candidates_token_count = 5
    mock_resp_second.usage_metadata.total_token_count = 15

    provider._generate = AsyncMock(side_effect=[mock_resp_first, mock_resp_second])

    result = await provider.generate(GenerationRequest(prompt="test"))
    assert result.text == "Fallback response"
    assert result.model == FALLBACK_MODEL
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 5
    assert result.usage.total_tokens == 15


@pytest.mark.asyncio
async def test_gemini_provider_fallback_also_fails_raises_without_loop():
    # Test that provider does not loop indefinitely if both models fail
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    mock_error = Exception("Service unavailable")
    provider._generate = AsyncMock(side_effect=[mock_error, mock_error])

    with pytest.raises(Exception, match="Service unavailable"):
        await provider.generate(GenerationRequest(prompt="test"))
    assert provider._generate.call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_non_503_error_raises_immediately():
    # Test that provider raises non-503 errors without fallback attempts
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    mock_error = Exception("Invalid argument")
    provider._generate = AsyncMock(side_effect=mock_error)

    with pytest.raises(Exception, match="Invalid argument"):
        await provider.generate(GenerationRequest(prompt="test"))
    assert provider._generate.call_count == 1