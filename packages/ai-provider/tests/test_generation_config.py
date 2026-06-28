from ai_provider.config import GenerationConfig


def test_generation_config_temperature_setting():
    """Verify that the temperature parameter is correctly set in GenerationConfig."""
    config = GenerationConfig(temperature=0.2)
    assert config.temperature == 0.2, "Temperature value not set correctly"


def test_generation_config_defaults():
    """Verify that unset parameters use their default values."""
    config = GenerationConfig()
    assert config.temperature == 0.7, "Default temperature should be 0.7"