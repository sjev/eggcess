""" test date and time functions """

import asyncio
import machine
import network

from timing import update_time, now
from test_helpers import run, run_async


# ----------------- tests -----------------


def test_connection():
    """test wifi connection"""
    wifi = network.WLAN(network.STA_IF)
    assert wifi.isconnected(), "Wifi not connected"


def test_now():
    year, hour = now()
    print(f"Year: {year}, Hour: {hour}")


# -------------- main ------------------
tests = [test_connection, test_now, lambda: update_time(max_attempts=5, retry_delay=1)]

print("Running test_time.py")

for test in tests:
    run(test)


async_tests = []
for test in async_tests:
    run_async(test, timeout=5)

print("Done.")
