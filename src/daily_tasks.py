"""
Tasks module for scheduling and executing daily tasks.
"""

import logger
import timing
import door


class Task:
    """A task that runs once a day at a specified time."""

    def __init__(self, name: str, exec_time: float | None):

        self.name = name
        self.exec_time = exec_time
        self.is_executed = False

    def main(self):
        """Main task function."""
        raise NotImplementedError

    def execute(self):
        """Execute the task if the current time matches the execution time."""
        if self.exec_time is None:
            return

        current_time = timing.now()

        if current_time >= self.exec_time and not self.is_executed:
            logger.info(f"Executing task: {self.name} {current_time=}")
            self.main()
            self.is_executed = True


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


def get_latest_task(tasks) -> Task | None:
    current_time = timing.now()
    # Filter tasks that are scheduled before or at current time.
    tasks_before = [task for task in tasks if task.exec_time <= current_time]
    if tasks_before:
        # Return the task with the maximum exec_time.
        return max(tasks_before, key=lambda task: task.exec_time)
    return None
