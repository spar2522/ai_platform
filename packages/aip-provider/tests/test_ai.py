import pytest

from aip_provider import AI


def test_local_ai_creation_should_succeed():
    ai = AI.local()
    assert ai is not None


def test_local_ai_with_model_override_should_use_specified_model():
    local_ai = AI.local(
        model="deepseek-r1:32b",
    )
    assert local_ai is not None
    assert local_ai._provider._model == "deepseek-r1:32b"


def test_constructor_with_local_provider_should_succeed():
    ai = AI(
        provider="local",
    )
    assert ai is not None


def test_constructor_with_invalid_provider_should_raise_error():
    with pytest.raises(ValueError):
        AI(
            provider="banana",
        )