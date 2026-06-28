from ai_provider import (
    AI,
    AIProvider,
    AIProviderConfig,
    AIResponse,
    Usage,
)
from ai_provider.generation_options import GenerationOptions


def test_public_api_exports_are_correct():
    """Verify that the public API exports all required classes and modules."""
    assert AI is not None, "AI class not found in public API exports"
    assert AIProvider is not None, "AIProvider class not None"
    assert AIProviderConfig is not None, "AIProviderConfig class not found in public API exports"
    assert GenerationOptions is not None, "GenerationOptions class not found in public API exports"
    assert AIResponse is not None, "AIResponse class not found in public API exports"
    assert Usage is not None, "Usage class not found in public API exports"