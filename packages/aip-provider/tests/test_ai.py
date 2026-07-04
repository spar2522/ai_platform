import pytest

from ai_provider import AI


def test_local_ai_creation():
    """Verify that a local AI instance can be created successfully."""
    ai = AI.local()
    assert ai is not None


def test_local_ai_with_model_override():
    """Verify that a local AI instance can be created with a custom model."""
    ai = AI.local(
        model="deepseek-r1:32b",
    )
    assert ai is not None
    assert ai._provider._model == "deepseek-r1:32b"


def test_generic_constructor_with_local_provider():
    """Verify that the generic constructor can create a local AI instance."""
    ai = AI(
        provider="local",
    )
    assert ai is not None


def test_invalid_provider_raises_error():
    """Verify that an invalid provider raises a ValueError."""
    with pytest.raises(ValueError):
        AI(
            provider="banana",
        )