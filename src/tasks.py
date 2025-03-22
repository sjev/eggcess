"""
Minimalistic task manager for scheduling daily tasks.

How it works:
* `Task` is a class that wraps a function, keeping track of execution.
* `TaskManager` is responsible for running tasks at specified times.
* Execution is synchronous - `TaskManager.execute()` checks for scheduled tasks and
                              runs them if needed.


"""

import time


class Task:
    """A task that runs once a day at a specified time."""

    def __init__(self, name, fcn, hour, minute) -> None:
        """
        Initialize a daily task.

        Args:
            name: Descriptive name for the task
            fcn: Function to execute when the task runs
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        self.name = name
        self.fcn = fcn
        self.hour = hour
        self.minute = minute
        self.execution_count = 0
        self.last_execution_day = -1  # Track the day to ensure once per day execution

    def should_execute(self) -> bool:
        """
        Check if task should execute based on current time.



        Returns:
            True if task should execute, False otherwise
        """
        # Extract time components
        _, _, day, hour, minute, _, _, _, _ = time.localtime()

        # Check if already executed today
        if day == self.last_execution_day:
            return False

        # Check if it's time to execute
        return hour >= self.hour and minute >= self.minute

    def execute(self) -> None:
        """
        Execute the task function and record execution.

        """
        self.fcn()
        self.execution_count += 1

        # Record the day of execution
        _, _, day, _, _, _, _, _, _ = time.localtime()
        self.last_execution_day = day


class TaskManager:
    """Manages and executes scheduled tasks."""

    def __init__(self) -> None:
        """Initialize the task manager with an empty task list."""
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """
        Add a task to the manager.

        Args:
            task: The task to add
        """
        self.tasks.append(task)

    def execute(self) -> None:
        """
        Check all tasks and execute those that are scheduled for the current time.
        """

        for task in self.tasks:
            if task.should_execute():
                try:
                    task.execute()
                except Exception as e:
                    print(f"Error executing task {task.name}: {str(e)}")
