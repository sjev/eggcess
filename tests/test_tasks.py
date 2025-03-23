import pytest
import daily_tasks
import door
from unittest.mock import Mock


class FakeDoor(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = door.STATE_CLOSED


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


def test_get_latest_task(mocker):
    open_task = daily_tasks.OpenDoorTask(exec_time=5.0, door=None)
    close_task = daily_tasks.CloseDoorTask(exec_time=10.0, door=None)
    tasks_list = [open_task, close_task]

    mocker.patch("daily_tasks.timing.now", return_value=11.0)
    latest_task = daily_tasks.get_latest_task(tasks_list)
    assert latest_task == close_task

    mocker.patch("daily_tasks.timing.now", return_value=6.0)
    latest_task = daily_tasks.get_latest_task(tasks_list)
    assert latest_task == open_task
