from ai_provider.config import GenerationConfig


def test_generation_config():

    config = GenerationConfig(
        temperature=0.2,
    )

    assert config.temperature == 0.2
