import pytest

from aip_provider import AI


def test_local_ai_creation():

    ai = AI.local()

    assert ai is not None


def test_local_ai_with_model_override():

    ai = AI.local(
        model="deepseek-r1:32b",
    )

    assert ai is not None
    assert ai._provider._model == "deepseek-r1:32b"


def test_generic_constructor():

    ai = AI(
        provider="local",
    )

    assert ai is not None


def test_invalid_provider():

    with pytest.raises(ValueError):
        AI(
            provider="banana",
        )
