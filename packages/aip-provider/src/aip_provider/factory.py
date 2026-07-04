from aip_provider.provider_type import Provider

from aip_provider.providers.dummy_provider import DummyProvider
from aip_provider.providers.gemini_provider import GeminiProvider
from aip_provider.providers.ollama_provider import OllamaProvider


class AIPProviderFactory:

    @staticmethod
    def create(config):
        """Create an AIP provider instance based on the configuration.

        Args:
            config: Configuration object containing the 'provider' attribute
                    specifying the type of provider to create.

        Returns:
            An instance of the corresponding AIP provider.

        Raises:
            ValueError: If the provider type is not supported or config is None.
        """
        if config is None:
            raise ValueError("Configuration cannot be None")
        providers = {
            Provider.OLLAMA: OllamaProvider,
            Provider.DUMMY: DummyProvider,
            Provider.GEMINI: GeminiProvider,
        }
        provider_class = providers.get(config.provider)
        if provider_class is None:
            raise ValueError(f"Unsupported provider {config.provider}")
        return provider_class(config)