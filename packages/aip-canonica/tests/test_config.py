from aip_canonica import configure
from aip_canonica.config import get_config


def test_configure():
    """Verify that configure sets the learning_enabled parameter to False."""
    configure(learning_enabled=False)
    assert get_config().learning_enabled is False


def test_configure_with_true():
    """Verify that configure sets the learning_enabled parameter to True."""
    configure(learning_enabled=True)
    assert get_config().learning_enabled is True