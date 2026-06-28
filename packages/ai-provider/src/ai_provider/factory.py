from ai_provider.provider_type import Provider

from ai_provider.providers.dummy_provider import DummyProvider


class AIProviderFactory:

    @staticmethod
    def create(config):

        match config.provider:

            case Provider.OLLAMA:
                return DummyProvider()

            case _:
                raise ValueError(f"Unsupported provider {config.provider}")
