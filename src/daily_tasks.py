"""
Tasks module for scheduling and executing daily tasks.
"""

import os
import time
import logger
import timing
import door
import sun


class Task:
    """A task that runs once a day at a specified time."""

    def __init__(self, name: str, exec_time: float | None):
        self.name = name
        self.exec_time = exec_time
        self._yday_executed = -1 # used to reset executed flag on new day
        self._exec_count = 0

    @property
    def exec_count(self) -> int:
        """Return the number of times the task has been executed."""
        return self._exec_count

    @property
    def is_executed(self) -> bool:
        """Returns True if the task has been executed today."""
        return self._yday_executed == time.localtime().tm_yday

    @is_executed.setter
    def is_executed(self, value: bool):
        """Set the executed flag."""
        if value:
            self._yday_executed = time.localtime().tm_yday
        else:
            self._yday_executed = -1

    def main(self):
        """Main task function."""
        raise NotImplementedError  # pragma: no cover

    def execute(self):
        """Execute the task if the current time matches the execution time.
        Automatically resets execution flag on a new day.
        """
        logger.debug(f"Executing: {self}")

        if self.exec_time is None:
            return

        current_time = timing.now()

        if current_time >= self.exec_time and not self.is_executed:
            logger.debug(f"Executing task: {self.name} {current_time=}")
            self.main()
            self._yday_executed = time.localtime().tm_yday
            self._exec_count += 1

    def __str__(self):
        return (
            f"{self.name} {self.exec_time=} {self.is_executed=} {self._yday_executed=}"
        )


class OpenDoorTask(Task):
    """Open the door at the specified time."""

    def __init__(self, exec_time: float | None, door: door.Door):
        super().__init__("open_door", exec_time)
        self.door = door

    def main(self):
        """Open the door."""
        if self.door.state == door.STATE_OPEN:
            return

        self.door.open()


class CloseDoorTask(Task):
    """Close the door at the specified time."""

    def __init__(self, exec_time: float | None, door: door.Door):
        super().__init__("close_door", exec_time)
        self.door = door

    def main(self):
        """Close the door."""
        if self.door.state == door.STATE_CLOSED:
            return

        self.door.close()


class SetClockTask(Task):
    """set clock from NTP server"""

    def __init__(self, exec_time: float = 1.0):
        super().__init__("set_clock", exec_time)

    def main(self):
        """Set the clock."""
        logger.info("Setting clock")
        try:
            timing.update_ntp_time()
        except timing.MaxRetriesExceeded:
            logger.error("Failed to set clock from NTP server")


class UpdateDoorTimesTask(Task):
    """Update open and close times from rise and set times"""

    def __init__(
        self, exec_time: float, open_task: OpenDoorTask, close_task: CloseDoorTask
    ):
        super().__init__("update_door_times", exec_time)
        self.open_task = open_task
        self.close_task = close_task

    def main(self):
        """Update open and close times."""

        if not timing.is_rtc_set():
            raise RuntimeError("RTC not set")

        ts = time.localtime()

        before_sunrise = float(os.getenv("BEFORE_SUNRISE", "0.0"))
        after_sunset = float(os.getenv("AFTER_SUNSET", "0.0"))
        not_before = float(os.getenv("NOT_BEFORE", "0.0"))

        # calculate sunrise and sunset times
        sunrise = sun.sunrise(ts.tm_year, ts.tm_mon, ts.tm_mday)
        sunset = sun.sunset(ts.tm_year, ts.tm_mon, ts.tm_mday)

        logger.info(f"sunrise: {timing.hours2str(sunrise)} sunset: {timing.hours2str(sunset)}")

        # limit open time to not before
        open_time = max(sunrise - before_sunrise, not_before)

        close_time = sunset + after_sunset

        logger.info(
            f"Updated door times: {timing.hours2str(open_time)}, {timing.hours2str(close_time)}"
        )
        self.open_task.exec_time = open_time
        self.close_task.exec_time = close_time


def init_open_close(open_task: Task, close_task: Task):
    """Initialize the open and close tasks."""

    if not timing.is_rtc_set():
        raise RuntimeError("RTC not set")

    now = timing.now()

    if open_task.exec_time is None or close_task.exec_time is None:
        raise ValueError("Open and close times must be set")

    if open_task.exec_time <= now < close_task.exec_time:
        open_task.execute()
    if now >= close_task.exec_time:
        open_task.is_executed = True  # skip open task
        close_task.execute()
