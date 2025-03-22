# conftest.py
import sys
from unittest.mock import MagicMock

# Immediately mock hardware/time modules
modules_to_mock = [
    "machine",
    "utime",
    "ntptime",
    "uln2003",
    "adafruit_ntp",
    "rtc",
    "socketpool",
    "wifi",
    "board",
]

for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

# Optionally, you can still have a fixture for any per-test setup
import pytest


@pytest.fixture(autouse=True)
def auto_mocker():
    yield
