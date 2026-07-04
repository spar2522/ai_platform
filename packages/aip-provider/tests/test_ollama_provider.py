import json

import httpx
import pytest

from aip_provider.config import AIProviderConfig
from aip_provider.generation_options import GenerationOptions
from aip_provider.generation_request import GenerationRequest
from aip_provider.models import AIResponse
from aip_provider.provider_type import Provider
from aip_provider.providers.ollama_provider import OllamaProvider

import httpx
import pytest


async def ollama_running() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:11434/api/tags",
                timeout=1,
            )

            return response.status_code == 200

    except Exception:
        return False


def create_provider(
    client: httpx.AsyncClient | None = None,
) -> OllamaProvider:

    config = AIProviderConfig(
        provider=Provider.OLLAMA,
        model="qwen3:14b",
    )

    return OllamaProvider(
        config=config,
        client=client,
    )


def test_provider_creation():

    provider = create_provider()

    assert provider is not None


def test_ollama_defaults():

    provider = create_provider()

    assert provider._model == "qwen3:14b"
    assert provider._base_url == "http://localhost:11434"
    assert provider._timeout_seconds == 120


def test_resolve_generation_options():

    config = AIProviderConfig(
        provider=Provider.OLLAMA,
        model="qwen3:14b",
        generation=GenerationOptions(
            temperature=0.7,
            stream=False,
        ),
    )

    provider = OllamaProvider(config)

    request = GenerationRequest(
        prompt="Hello",
        options=GenerationOptions(
            temperature=0.2,
        ),
    )

    options = provider._resolve_generation_options(request)

    assert options.temperature == 0.2

    assert options.stream is False


def test_build_payload():

    provider = create_provider()

    request = GenerationRequest(
        prompt="Hello",
        system_prompt="You are helpful.",
        options=GenerationOptions(
            temperature=0.5,
            max_tokens=200,
            top_p=0.8,
        ),
    )

    payload = provider._build_payload(request)

    assert payload["model"] == "qwen3:14b"

    assert payload["stream"] is False

    assert len(payload["messages"]) == 2

    assert payload["messages"][0]["role"] == "system"

    assert payload["messages"][1]["role"] == "user"

    assert payload["options"]["temperature"] == 0.5

    assert payload["options"]["num_predict"] == 200

    assert payload["options"]["top_p"] == 0.8


def test_build_payload_without_optional_fields():

    provider = create_provider()

    request = GenerationRequest(prompt="Hello")

    payload = provider._build_payload(request)

    assert payload["messages"] == [
        {
            "role": "user",
            "content": "Hello",
        }
    ]

    assert "options" not in payload


@pytest.mark.asyncio
async def test_generate_mock():

    response_body = {
        "model": "qwen3:14b",
        "done_reason": "stop",
        "message": {
            "role": "assistant",
            "content": "Hello there!",
        },
    }

    def handler(request: httpx.Request):

        return httpx.Response(
            status_code=200,
            json=response_body,
        )

    transport = httpx.MockTransport(handler)

    client = httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost:11434",
    )

    provider = create_provider(client)

    response = await provider.generate(
        GenerationRequest(
            prompt="Hello",
        )
    )

    assert isinstance(response, AIResponse)

    assert response.text == "Hello there!"

    assert response.model == "qwen3:14b"

    assert response.finish_reason == "stop"

    await provider.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_real():

    if not await ollama_running():
        pytest.skip("""
Ollama server is not running.

Start it with:

    ollama serve

Verify:

    curl http://localhost:11434/api/tags

Then rerun the test using by running 'pytest'

""")
    provider = create_provider()

    response = await provider.generate(
        GenerationRequest(
            prompt="Reply only with the word hello.",
        )
    )

    assert isinstance(response, AIResponse)

    assert len(response.text) > 0

    assert response.model == "qwen3:14b"

    await provider.close()
