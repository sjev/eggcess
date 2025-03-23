"""
Tasks module for scheduling and executing daily tasks.
"""

import time
import logger
import timing
import door


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
            logger.info(f"Executing task: {self.name} {current_time=}")
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

        logger.info("Opening door")
        self.door.open()
        self.door.save_state()


class CloseDoorTask(Task):
    """Close the door at the specified time."""

    def __init__(self, exec_time: float | None, door: door.Door):
        super().__init__("close_door", exec_time)
        self.door = door

    def main(self):
        """Close the door."""
        if self.door.state == door.STATE_CLOSED:
            return

        logger.info("Closing door")
        self.door.close()
        self.door.save_state()


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


def init_open_close(open_task: Task, close_task: Task):
    """Initialize the open and close tasks."""
    now = timing.now()

    if open_task.exec_time is None or close_task.exec_time is None:
        raise ValueError("Open and close times must be set")

    if open_task.exec_time <= now < close_task.exec_time:
        open_task.execute()
    if now >= close_task.exec_time:
        open_task.is_executed = True  # skip open task
        close_task.execute()
