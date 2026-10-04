from unittest.mock import AsyncMock, MagicMock
import pytest

from aip_provider.config import AIProviderConfig
from aip_provider.generation_request import GenerationRequest
from aip_provider.provider_type import Provider
from aip_provider.providers.gemini_provider import DEFAULT_MODEL, FALLBACK_MODEL, GeminiProvider


def test_gemini_provider_init_with_explicit_key():
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="explicit-test-key",
    )
    provider = GeminiProvider(config)
    assert provider._model == DEFAULT_MODEL
    assert provider._model == "gemini-3.8-flash"


def test_gemini_provider_init_with_env_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-test-key")
    config = AIProviderConfig(
        provider=Provider.GEMINI,
    )
    provider = GeminiProvider(config)
    assert provider._model == "gemini-3.8-flash"


def test_gemini_provider_init_without_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    config = AIProviderConfig(
        provider=Provider.GEMINI,
    )
    with pytest.raises(ValueError, match="Gemini requires an API key"):
        GeminiProvider(config)


@pytest.mark.asyncio
async def test_gemini_provider_generate_with_usage():
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

    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    req = GenerationRequest(prompt="Say hi")
    res = await provider.generate(req)

    assert res.text == "Hello world"
    assert res.model == "gemini-3.8-flash"
    assert res.usage is not None
    assert res.usage.prompt_tokens == 15
    assert res.usage.completion_tokens == 8
    assert res.usage.total_tokens == 23


@pytest.mark.asyncio
async def test_gemini_provider_fallback_on_503():
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    mock_resp = MagicMock()
    mock_resp.text = "Fallback success"
    mock_resp.usage_metadata = None

    # First call fails with 503 high demand, second call succeeds with fallback model
    provider._client.aio.models.generate_content = AsyncMock(
        side_effect=[
            Exception("503 UNAVAILABLE. This model is currently experiencing high demand."),
            mock_resp,
        ]
    )

    req = GenerationRequest(prompt="Say hi")
    res = await provider.generate(req)

    assert res.text == "Fallback success"
    assert res.model == FALLBACK_MODEL
    assert res.model == "gemini-3.5-flash"
    assert provider._client.aio.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_fallback_also_fails_raises_without_loop():
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    # Both primary and fallback models throw 503
    provider._client.aio.models.generate_content = AsyncMock(
        side_effect=[
            Exception("503 UNAVAILABLE. Primary model experiencing high demand."),
            Exception("503 UNAVAILABLE. Fallback model experiencing high demand."),
        ]
    )

    req = GenerationRequest(prompt="Say hi")

    with pytest.raises(Exception, match="Fallback model experiencing high demand"):
        await provider.generate(req)

    # Exactly 2 calls made: primary then fallback; no endless loop
    assert provider._client.aio.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_gemini_provider_non_503_error_raises_immediately():
    config = AIProviderConfig(
        provider=Provider.GEMINI,
        api_key="test-key",
    )
    provider = GeminiProvider(config)

    provider._client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("400 INVALID_ARGUMENT: Invalid parameter")
    )

    req = GenerationRequest(prompt="Say hi")

    with pytest.raises(Exception, match="400 INVALID_ARGUMENT"):
        await provider.generate(req)

    # Exactly 1 call made; no fallback attempt for non-503 errors
    assert provider._client.aio.models.generate_content.call_count == 1