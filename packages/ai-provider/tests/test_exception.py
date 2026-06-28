from ai_provider.exceptions import AIProviderException


def test_exception():

    assert issubclass(
        AIProviderException,
        Exception,
    )
