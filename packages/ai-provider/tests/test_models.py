from ai_provider.models import AIResponse
from ai_provider.models import Usage


def test_ai_response():

    response = AIResponse(
        text="Hello",
        model="qwen3",
    )

    assert response.text == "Hello"
    assert response.model == "qwen3"


def test_usage():

    usage = Usage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )

    assert usage.total_tokens == 30
