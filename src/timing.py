"""
time-related functions

* update RTC
* read csv and return open and close times for today
"""

import asyncio
import utime as time
import machine
import ntptime
import logger

DATA_FILE = "sun_lut.csv"


class MaxRetriesExceeded(Exception):
    pass


def extract_floats_from_file(
    target_date: str, file_path: str = DATA_FILE
) -> tuple[float, float]:
    """extract the open and close times from the csv file for the target date"""
    print(f"extracting floats from file {file_path} for date {target_date}")
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(",")
            date = parts[0]
            if date == target_date:
                # Extracting the two float values
                float1 = float(parts[1])
                float2 = float(parts[2])
                return float1, float2
    raise ValueError("Date not found in file")


async def update_time(max_attempts=10, retry_delay=5):
    """update the RTC time from NTP server"""

    attempts = 0

    while attempts < max_attempts:
        logger.info(f"Updating time attempt {attempts + 1}")
        try:
            # Create an RTC object
            rtc = machine.RTC()

            # Sync time with NTP server
            ntptime.settime()

            # The time is set in UTC by default
            utc_time = rtc.datetime()

            # Print the UTC time
            logger.info("UTC Time:", utc_time)

            attempts = 0  # reset attempts
        except Exception as e:
            attempts += 1
            logger.error(f"Error updating time:  {type(e).__name__}: {e}")
            logger.info(f"Sleeping for {retry_delay} seconds")
            await asyncio.sleep(retry_delay)
        return

    # if we get here, we have exceeded the max attempts, raise an exception
    raise MaxRetriesExceeded("Failed to update time")


def time_str():
    """Format the time as 'year-month-date hh:mm:ss'"""
    current_time = time.localtime()
    formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        *current_time[0:6]
    )
    return formatted_time


def hours2str(hours: float) -> str:
    """Convert decimal hours to string, including hours, minutes, and seconds."""
    # Extract whole hours and remaining fractional hour
    whole_hours = int(hours)
    fractional_hours = hours % 1

    # Convert fractional hour to minutes
    minutes = int(fractional_hours * 60)
    # Calculate remaining fractional minutes
    fractional_minutes = (fractional_hours * 60) % 1

    # Convert remaining fractional minutes to seconds
    seconds = int(fractional_minutes * 60)

    return f"{whole_hours:02}:{minutes:02}:{seconds:02}"


def now() -> tuple[str, float]:
    """Return the current date as string and time as decimal hours"""
    rtc = machine.RTC()
    date = rtc.datetime()
    year, month, day = date[0], date[1], date[2]
    hour, minute, second = date[4], date[5], date[6]

    # check that time is not 2000-01-01
    assert year > 2000, "RTC not set"

    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    time_decimal = hour + minute / 60 + second / 3600

    return date_str, time_decimal


if __name__ == "__main__":
    today, now_time = now()
    print(f"Today: {today}, Now: {now_time}")

    test_dates = [today, "2030-02-27"]
    for test_date in test_dates:
        print(f"Testing date: {test_date}")
        t_start = time.ticks_ms()
        open_time, close_time = extract_floats_from_file(test_date)
        print(f"Time to read file: {time.ticks_ms() - t_start:.3f} ms")
        print(f"Open time: {open_time}, Close time: {close_time}")
