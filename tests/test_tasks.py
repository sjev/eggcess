import pytest
import time
import daily_tasks
import door
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def patch_logger_log_to_file(mocker):
    mocker.patch("logger.log_to_file", new=Mock())


@pytest.fixture(autouse=True)
def patch_rtc_is_set(mocker):
    mocker.patch("daily_tasks.timing.is_rtc_set", return_value=True)


class FakeDoor(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = door.STATE_CLOSED


# Dummy task subclass for testing the is_executed property behavior.
class DummyTask(daily_tasks.Task):
    def __init__(self, exec_time: float | None):
        super().__init__("dummy_task", exec_time)
        self.executed_flag = False

    def main(self):
        self.executed_flag = True


def test_skip_task_when_exec_time_is_none(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)

    task = DummyTask(None)
    task.execute()
    assert not task.is_executed


def test_execute_task_when_exec_time_is_now(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)

    task = DummyTask(10.0)
    task.execute()
    assert task.is_executed


def test_open_door_task_executes_when_door_closed(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    task = daily_tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_any_call("Opening door")
    assert task.is_executed


def test_open_door_task_does_not_execute_before_time(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=3.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    task = daily_tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_not_called()
    assert not task.is_executed


def test_open_door_task_skips_when_door_already_open(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    fake_door.state = door.STATE_OPEN

    task = daily_tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    for call in mock_logger.call_args_list:
        args, _ = call
        assert "Opening door" not in args[0]
    assert task.is_executed


def test_close_door_task_executes_when_door_open(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    fake_door.state = door.STATE_OPEN

    task = daily_tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_any_call("Closing door")
    assert task.is_executed


def test_close_door_task_does_not_execute_before_time(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=3.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    fake_door.state = door.STATE_OPEN

    task = daily_tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_not_called()
    assert not task.is_executed


def test_close_door_task_skips_when_door_already_closed(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    fake_door.state = door.STATE_CLOSED

    task = daily_tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    for call in mock_logger.call_args_list:
        args, _ = call
        assert "Closing door" not in args[0]
    assert task.is_executed


def test_task_does_not_execute_twice(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("daily_tasks.logger.info")

    fake_door = FakeDoor()
    fake_door.state = door.STATE_OPEN

    task = daily_tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.reset_mock()
    task.execute()

    mock_logger.assert_not_called()


# -----------------------set clock task-----------------------
def test_set_clock_task_success(mocker):
    # Ensure the task executes successfully.
    mocker.patch("daily_tasks.timing.now", return_value=2.0)
    update_ntp_mock = mocker.patch("daily_tasks.timing.update_ntp_time")
    mock_info = mocker.patch("daily_tasks.logger.info")
    mock_error = mocker.patch("daily_tasks.logger.error")

    task = daily_tasks.SetClockTask(exec_time=1.0)
    task.execute()

    # Verify that "Setting clock" is logged and the NTP update was called.
    mock_info.assert_any_call("Setting clock")
    update_ntp_mock.assert_called_once()
    mock_error.assert_not_called()
    assert task.is_executed


def test_set_clock_task_failure(mocker):
    # Simulate a failure in updating the clock.
    mocker.patch("daily_tasks.timing.now", return_value=2.0)
    mocker.patch(
        "daily_tasks.timing.update_ntp_time",
        side_effect=daily_tasks.timing.MaxRetriesExceeded,
    )
    mock_info = mocker.patch("daily_tasks.logger.info")
    mock_error = mocker.patch("daily_tasks.logger.error")

    task = daily_tasks.SetClockTask(exec_time=1.0)
    task.execute()

    # Verify that "Setting clock" is logged, then the error is logged.
    mock_info.assert_any_call("Setting clock")
    mock_error.assert_any_call("Failed to set clock from NTP server")
    assert task.is_executed


# -----------------------test daily reset-----------------------


def fake_localtime(day: int):
    """Helper to create a fake time.struct_time with the given day-of-year."""
    # (year, month, day, hour, minute, second, weekday, yearday, isdst)
    return time.struct_time((2025, 1, 1, 0, 0, 0, 0, day, 0))


def test_is_executed_default():
    """Ensure that before execution, is_executed is False (default _last_executed = -1)."""
    task = DummyTask(5.0)
    assert not task.is_executed, "Task should not be marked as executed before running."


def test_task_execution_resets_is_executed(mocker):
    """
    Test that after execution, is_executed becomes True,
    and when a new day is simulated, is_executed becomes False.
    """
    # Simulate day 100 for execution.
    mocker.patch("time.localtime", return_value=fake_localtime(100))
    mocker.patch("daily_tasks.timing.now", return_value=10.0)

    task = DummyTask(5.0)
    assert not task.is_executed, "Initially, task should not be executed."

    task.execute()
    assert task.executed_flag, "Task main() should have been called."
    assert task.is_executed, "After execution, task should be marked as executed."

    # Now simulate a new day (day 101); is_executed should automatically reset.
    mocker.patch("time.localtime", return_value=fake_localtime(101))
    assert not task.is_executed, "On a new day, task should not be marked as executed."


# -----------------------logic test-----------------------
def test_open_should_not_run_after_close(mocker):
    mocker.patch("daily_tasks.timing.now", return_value=19.0)

    fake_door = FakeDoor()
    fake_door.state = door.STATE_CLOSED

    open_task = DummyTask(exec_time=6.0)
    close_task = DummyTask(exec_time=18.0)

    daily_tasks.init_open_close(open_task, close_task)

    # simulate loop
    open_task.execute()
    close_task.execute()

    assert open_task.is_executed
    assert close_task.is_executed

    assert not open_task.executed_flag
    assert close_task.executed_flag
