"""
time-related functions

* update RTC
* read csv and return open and close times for today
"""
import asyncio
import utime as time
import machine
import ntptime

DATA_FILE = "sun_lut.csv"


def extract_floats_from_file(
    target_date: str, file_path: str = DATA_FILE
) -> tuple[float, float]:
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
        print(f"Updating time attempt {attempts + 1}")
        try:
            # Create an RTC object
            rtc = machine.RTC()

            # Sync time with NTP server
            ntptime.settime()

            # The time is set in UTC by default
            utc_time = rtc.datetime()

            # Print the UTC time
            print("UTC Time:", utc_time)

            attempts = 0  # reset attempts
        except Exception as e:
            attempts += 1
            print(f"Error updating time:  {type(e).__name__}: {e}")
            print(f"Sleeping for {retry_delay} seconds")
            await asyncio.sleep(retry_delay)
        return

    # if we get here, we have exceeded the max attempts, raise an exception
    raise RuntimeError("Failed to update time")


def time_str():
    """Format the time as 'year-month-date hh:mm:ss'"""
    current_time = time.localtime()
    formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        *current_time[0:6]
    )
    return formatted_time


def hours2str(hours: float) -> str:
    """Convert decimal hours to string"""
    return f"{int(hours):02}:{int((hours % 1) * 60):02}"


def now() -> tuple[str, float]:
    """Return the current date as string and time as decimal hours"""
    rtc = machine.RTC()
    date = rtc.datetime()
    year = date[0]
    month = date[1]
    day = date[2]
    hour = date[4]
    minute = date[5]
    second = date[6]

    # check that time is not 2000-01-01
    assert year > 2000, "RTC not set"

    return f"{year}-{month}-{day}", hour + minute / 60 + second / 3600


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
