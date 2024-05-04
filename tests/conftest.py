# type: ignore

import pytest
from unittest.mock import MagicMock
import sys
import time


# Fixture that runs once per test session
@pytest.fixture(scope="session", autouse=True)
def mock_hardware_modules():
    # Mock the hardware-specific modules

    sys.modules["machine"] = MagicMock()
    sys.modules["utime"] = MagicMock()
    sys.modules["ntptime"] = MagicMock()

    # Mock the Stepper class from the uln2003 module
    stepper_mock = MagicMock()
    uln2003 = MagicMock()
    uln2003.Stepper.return_value = stepper_mock

    sys.modules["uln2003"] = uln2003

    # Optional: Cleanup after the test session is done
    yield  # This allows the test session to run with the mocks in place

    # Cleanup
    del sys.modules["machine"]
    del sys.modules["utime"]
    del sys.modules["ntptime"]
    del sys.modules["uln2003"]
