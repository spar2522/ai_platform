import pytest

from ai_provider import AI


def test_local_ai_creation():
    """
    Test that AI.local() returns a valid AI instance.
    """
    ai = AI.local()
    assert ai is not None


def test_local_ai_with_model_override():
    """
    Test that AI.local() accepts a model override and sets it correctly.
    """
    ai = AI.local(model="deepseek-r1:32b")
    assert ai is not None
    assert ai._provider._model == "deepseek-r1:32b"


def test_ai_constructor_with_local_provider():
    """
    Test that the AI constructor with provider="local" returns a valid instance.
    """
    ai = AI(provider="local")
    assert ai is not None
    assert ai._provider._model == "qwen3"  # Default model


def test_invalid_provider():
    """
    Test that using an invalid provider raises a ValueError.
    """
    with pytest.raises(ValueError, match="Invalid provider: banana"):
        AI(provider="banana")