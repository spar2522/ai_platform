from ai_provider.provider_type import Provider

from ai_provider.providers.dummy_provider import DummyProvider
from ai_provider.providers.gemini_provider import GeminiProvider
from ai_provider.providers.ollama_provider import OllamaProvider


class AIProviderFactory:
    PROVIDERS = {
        Provider.OLLAMA: OllamaProvider,
        Provider.DUMMY: DummyProvider,
        Provider.GEMINI: GeminiProvider,
    }

    @staticmethod
    def create(config):
        """Create an AI provider instance based on the configuration.

        Args:
            config: An object with a 'provider' attribute specifying the type of AI provider to create.

        Returns:
            An instance of the corresponding AI provider.

        Raises:
            ValueError: If the provider type is not supported (i.e., not in the PROVIDERS dictionary).
        """
        provider_class = AIProviderFactory.PROVIDERS.get(config.provider)
        if provider_class is None:
            raise ValueError(f"Unsupported provider {config.provider}")
        return provider_class(config)