# SPDX-FileCopyrightText: 2022 Scott Shawcroft for Adafruit Industries
# SPDX-License-Identifier: MIT

"""Example demonstrating how to set the realtime clock (RTC) based on NTP time."""

import time

import rtc
import socketpool
import wifi

import adafruit_ntp


if not wifi.radio.connected:
    raise RuntimeError("Wifi not connected")

pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=0)

# NOTE: This changes the system time so make sure you aren't assuming that time
# doesn't jump.
rtc.RTC().datetime = ntp.datetime

while True:
    print(time.localtime())
    time.sleep(1)
