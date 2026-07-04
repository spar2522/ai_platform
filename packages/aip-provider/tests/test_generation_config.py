from aip_provider.generation_options import GenerationOptions


def test_generation_config():
    """Verify that GenerationOptions correctly initializes with specified temperature."""
    config = GenerationOptions(
        temperature=0.2,
    )

    assert config.temperature == 0.2