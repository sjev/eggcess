"""
time-related functions

* update RTC
* read csv and return open and close times for today
"""

import time
import adafruit_ntp
import rtc
import socketpool
import wifi
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


def update_ntp_time(max_attempts=10, retry_delay=5):
    """update the RTC time from NTP server"""

    pool = socketpool.SocketPool(wifi.radio)
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)

    attempts = 0

    while attempts < max_attempts:
        logger.debug(f"Updating time attempt {attempts + 1}")
        try:
            rtc.RTC().datetime = ntp.datetime

            # Print the UTC time
            print("UTC Time:", time.localtime())

            attempts = 0  # reset attempts
        except Exception as e:
            attempts += 1
            logger.debug(f"Error updating time:  {type(e).__name__}: {e}")
            logger.debug(f"Sleeping for {retry_delay} seconds")
            time.sleep(retry_delay)
        return

    # if we get here, we have exceeded the max attempts, raise an exception
    raise MaxRetriesExceeded("Failed to update time")


def is_rtc_set() -> bool:
    """Check if the RTC is set"""
    return rtc.RTC().datetime.tm_year > 2000


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


def date() -> str:
    """Return the current date as string"""

    ts = time.localtime()

    return f"{ts.tm_year:04d}-{ts.tm_mon:02d}-{ts.tm_mday:02d}"


def now() -> float:
    """Return the current time as decimal hours"""

    ts = time.localtime()

    return ts.tm_hour + ts.tm_min / 60 + ts.tm_sec / 3600


# ------------------------------ testing --------------------------------
def test() -> None:
    """basic testing function"""
    print("Running test function")
    update_ntp_time()
    today = date()
    now_time = now()
    print(f"Today: {today}, Now: {now_time}")

    test_dates = [today, "2030-02-27"]
    for test_date in test_dates:
        print(f"Testing date: {test_date}")
        t_start = time.monotonic()
        open_time, close_time = extract_floats_from_file(test_date)
        print(f"Time to read file: {time.monotonic() - t_start:.3f} s")
        print(f"Open time: {open_time}, Close time: {close_time}")


if __name__ == "__main__":
    test()
