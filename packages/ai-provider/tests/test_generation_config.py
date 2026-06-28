from ai_provider.generation_options import GenerationOptions


def test_generation_config():
    """Verify GenerationOptions initialization and attribute access."""
    # Test basic parameter setting
    config = GenerationOptions(
        temperature=0.2,
        max_tokens=100,
        top_p=0.9,
        stop_sequences=["\n", "END"],
        presence_penalty=0.5,
        frequency_penalty=0.3,
    )

    assert config.temperature == 0.2
    assert config.max_tokens == 100
    assert config.top_p == 0.9
    assert config.stop_sequences == ["\n", "END"]
    assert config.presence_penalty == 0.5
    assert config.frequency_penalty == 0.3

    # Test default values for unset parameters
    default_config = GenerationOptions()
    assert default_config.temperature is None
    assert default_config.max_tokens is None
    assert default_config.top_p is None
    assert default_config.stop_sequences is None
    assert default_config.presence_penalty is None
    assert default_config.frequency_penalty is None

    # Test parameter type enforcement
    try:
        GenerationOptions(temperature="high")
    except ValueError:
        pass  # Expected validation error for invalid temperature type
    else:
        assert False, "Invalid temperature type should raise ValueError"

    # Test parameter value range enforcement
    try:
        GenerationOptions(temperature=2.0)
    except ValueError:
        pass  # Expected validation error for temperature out of range
    else:
        assert False, "Temperature out of range should raise ValueError"