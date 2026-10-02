import pytest

import timing


class FakeNTP:
    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    @property
    def datetime(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise OSError("timeout")
        return "now"


def test_ntp_retries_then_succeeds(mocker):
    ntp = FakeNTP(failures=1)
    mocker.patch("timing.adafruit_ntp.NTP", return_value=ntp)

    timing.update_ntp_time(max_attempts=3, retry_delay=0)

    assert ntp.calls == 2


def test_ntp_raises_after_max_attempts(mocker):
    ntp = FakeNTP(failures=99)
    mocker.patch("timing.adafruit_ntp.NTP", return_value=ntp)

    with pytest.raises(timing.MaxRetriesExceeded):
        timing.update_ntp_time(max_attempts=3, retry_delay=0)

    assert ntp.calls == 3
