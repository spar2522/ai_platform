from ai_provider.factory import AIProviderFactory
from ai_provider.config import AIProviderConfig
from ai_provider.base_provider import AIProvider


class AI:
    """Public entry point for creating AI providers."""

    @staticmethod
    def create(config: AIProviderConfig) -> AIProvider:
        return AIProviderFactory.create(config)
