"""
Tasks module for scheduling and executing daily tasks.
"""

import os
import time
import logger
import timing
import door
import sun

BEFORE_SUNRISE = os.getenv("BEFORE_SUNRISE", 0.0)
AFTER_SUNSET = os.getenv("AFTER_SUNSET", 0.0)


class Task:
    """A task that runs once a day at a specified time."""

    def __init__(self, name: str, exec_time: float | None):
        self.name = name
        self.exec_time = exec_time
        self._last_executed = -1

    @property
    def is_executed(self) -> bool:
        """Returns True if the task has been executed today."""
        return self._last_executed == time.localtime().tm_yday

    @is_executed.setter
    def is_executed(self, value: bool):
        """Set the executed flag to True."""
        self._last_executed = time.localtime().tm_yday

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
            self._last_executed = time.localtime().tm_yday

    def __str__(self):
        return (
            f"{self.name} {self.exec_time=} {self.is_executed=} {self._last_executed=}"
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

        ts = time.localtime()

        open_time = sun.sunrise(ts.tm_year, ts.tm_mon, ts.tm_mday) - BEFORE_SUNRISE
        close_time = sun.sunset(ts.tm_year, ts.tm_mon, ts.tm_mday) + AFTER_SUNSET

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
