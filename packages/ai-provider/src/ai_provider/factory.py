from ai_provider.provider_type import Provider

from ai_provider.providers.dummy_provider import DummyProvider
from ai_provider.providers.ollama_provider import OllamaProvider


class AIProviderFactory:

    @staticmethod
    def create(config: object) -> object:
        """Create an AI provider instance based on the configuration.

        Args:
            config: Configuration object with a 'provider' attribute of type Provider.

        Returns:
            An instance of the corresponding AI provider.

        Raises:
            ValueError: If the provider type is not supported.
        """
        provider_mapping = {
            Provider.OLLAMA: OllamaProvider,
            Provider.DUMMY: DummyProvider,
        }
        provider_class = provider_mapping.get(config.provider)
        if provider_class is None:
            raise ValueError(f"Unsupported provider {config.provider}")
        return provider_class(config)