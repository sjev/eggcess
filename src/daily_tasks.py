"""
Tasks module for scheduling and executing daily tasks.
"""

import logger
import timing
import door


class Task:
    """A task that runs once a day at a specified time."""

    def __init__(self, name: str, exec_time: float):

        self.name = name
        self.exec_time = exec_time
        self.is_executed = False

    def main(self):
        """Main task function."""
        raise NotImplementedError

    def execute(self):
        """Execute the task if the current time matches the execution time."""
        current_time = timing.now()

        if current_time >= self.exec_time and not self.is_executed:
            logger.info(f"Executing task: {self.name} {current_time=}")
            self.main()
            self.is_executed = True


class OpenDoorTask(Task):
    """Open the door at the specified time."""

    def __init__(self, exec_time: float, door: door.Door):
        super().__init__("open_door", exec_time)
        self.door = door

    def main(self):
        """Open the door."""
        if self.door.state == door.STATE_OPEN:
            return

        logger.info("Opening door")


class CloseDoorTask(Task):
    """Close the door at the specified time."""

    def __init__(self, exec_time: float, door: door.Door):
        super().__init__("close_door", exec_time)
        self.door = door

    def main(self):
        """Close the door."""
        if self.door.state == door.STATE_CLOSED:
            return

        logger.info("Closing door")


def get_latest_task(tasks):
    current_time = timing.now()
    # Filter tasks that are scheduled before or at current time.
    tasks_before = [task for task in tasks if task.exec_time <= current_time]
    if tasks_before:
        # Return the task with the maximum exec_time.
        return max(tasks_before, key=lambda task: task.exec_time)
    return None
