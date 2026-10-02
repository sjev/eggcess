import time
import pytest

import timing


def test_utc_offset_follows_eu_summer_time():
    winter = time.struct_time((2026, 1, 15, 12, 0, 0, 3, 15, -1))
    summer = time.struct_time((2026, 7, 15, 12, 0, 0, 2, 196, -1))

    assert timing.utc_offset(winter, std_offset=1.0) == 1.0
    assert timing.utc_offset(summer, std_offset=1.0) == 2.0


def test_summer_time_starts_last_sunday_of_march_0100_utc():
    before = (2026, 3, 29, 0, 59, 0, 6, 88)
    after = (2026, 3, 29, 1, 0, 0, 6, 88)

    assert timing.utc_offset(before) == 1.0
    assert timing.utc_offset(after) == 2.0


def test_summer_time_ends_last_sunday_of_october_0100_utc():
    before = (2026, 10, 25, 0, 59, 0, 6, 298)
    after = (2026, 10, 25, 1, 0, 0, 6, 298)

    assert timing.utc_offset(before) == 2.0
    assert timing.utc_offset(after) == 1.0


def test_last_sunday_matches_calendar():
    assert timing._last_sunday(2026, 3) == 29
    assert timing._last_sunday(2026, 10) == 25
    assert timing._last_sunday(2027, 3) == 28
    assert timing._last_sunday(2027, 10) == 31
    assert timing._last_sunday(2028, 3) == 26  # leap year


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
