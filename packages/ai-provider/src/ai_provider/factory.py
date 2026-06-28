from ai_provider.provider_type import Provider

from ai_provider.providers.dummy_provider import DummyProvider


class AIProviderFactory:

    @staticmethod
    def create(config):
        """Create an AI provider instance based on the configuration.

        Args:
            config: Configuration object containing the provider type.

        Returns:
            An instance of the corresponding AI provider.

        Raises:
            ValueError: If the provider type is not supported.
        """
        providers = {
            Provider.OLLAMA: DummyProvider,
        }
        provider_class = providers.get(config.provider)
        if provider_class is None:
            raise ValueError(f"Unsupported provider {config.provider}")
        return provider_class()