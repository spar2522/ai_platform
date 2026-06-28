from ai_provider.factory import AIProviderFactory
from ai_provider.config import AIProviderConfig
from ai_provider.base_provider import AIProvider


class AI:
    """Public entry point for creating AI providers.

    This class serves as a facade to the AIProviderFactory, allowing users to
    create AI provider instances based on a configuration object.
    """

    @staticmethod
    def create(config: AIProviderConfig) -> AIProvider:
        """Creates an AI provider instance based on the given configuration.

        Args:
            config (AIProviderConfig): The configuration object specifying the AI provider to create.
                This configuration is used by the factory to determine which provider to instantiate.

        Returns:
            AIProvider: An instance of the AI provider as specified in the configuration.

        Raises:
            ValueError: If the configuration is invalid or the provider type is not supported.
        """
        return AIProviderFactory.create(config)