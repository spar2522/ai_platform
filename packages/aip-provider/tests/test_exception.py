from aip_provider.exceptions import AIProviderException


def test_aip_provider_exception_is_subclass_of_exception():
    """Verify that AIProviderException is a subclass of the built-in Exception class."""
    assert issubclass(AIProviderException, Exception)