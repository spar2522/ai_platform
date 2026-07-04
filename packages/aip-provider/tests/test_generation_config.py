from aip_provider.generation_options import GenerationOptions


def test_generation_options_initialization_with_temperature():
    """Test that GenerationOptions initializes with specified temperature."""
    config = GenerationOptions(temperature=0.2)
    assert config.temperature == 0.2


def test_generation_options_initialization_with_max_tokens():
    """Test that GenerationOptions initializes with specified max_tokens."""
    config = GenerationOptions(max_tokens=150)
    assert config.max_tokens == 150


def test_generation_options_initialization_with_top_p():
    """Test that GenerationOptions initializes with specified top_p."""
    config = GenerationOptions(top_p=0.8)
    assert config.top_p == 0.8


def test_generation_options_initialization_with_presence_penalty():
    """Test that GenerationOptions initializes with specified presence_penalty."""
    config = GenerationOptions(presence_penalty=0.5)
    assert config.presence_penalty == 0.5


def test_generation_options_initialization_with_default_values():
    """Test that GenerationOptions uses default values when not specified."""
    config = GenerationOptions()
    assert config.temperature == 0.7
    assert config.max_tokens == 200
    assert config.top_p == 1.0
    assert config.presence_penalty == 0.0