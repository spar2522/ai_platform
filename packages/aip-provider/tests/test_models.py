from aip_provider.models import AIResponse
from aip_provider.models import Usage


def test_ai_response_initialization():
    """Test that AIResponse is initialized with correct text and model."""
    response = AIResponse(
        text="Hello",
        model="qwen3",
    )

    assert response.text == "Hello"
    assert response.model == "qwen3"


def test_usage_initialization():
    """Test that Usage is initialized with correct token values."""
    usage_instance = Usage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )

    assert usage_instance.total_tokens == 30
