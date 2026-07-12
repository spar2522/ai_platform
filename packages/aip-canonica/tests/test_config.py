from aip_canonica import configure
from aip_canonica.config import get_config


def test_configure():
    configure(learning_enabled=False)

    assert get_config().learning_enabled is False
