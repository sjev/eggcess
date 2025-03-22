import pytest
import tasks
import door


# Test for OpenDoorTask when door is closed and time has reached exec_time.
def test_open_door_task_executes_when_door_closed(mocker):
    # Set current time after exec_time.
    mocker.patch("tasks.timing.now", return_value=10.0)
    # Patch logger to capture output.
    mock_logger = mocker.patch("tasks.logger.info")

    # Create a fake door with state CLOSED.
    class FakeDoor:
        state = door.STATE_CLOSED

    fake_door = FakeDoor()

    task = tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    # Should log "Opening door"
    mock_logger.assert_any_call("Opening door")
    assert task.is_executed


# Test for OpenDoorTask when current time is before exec_time.
def test_open_door_task_does_not_execute_before_time(mocker):
    mocker.patch("tasks.timing.now", return_value=3.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_CLOSED

    fake_door = FakeDoor()

    task = tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    # logger.info should not be called.
    mock_logger.assert_not_called()
    assert not task.is_executed


# Test for OpenDoorTask when door is already open.
def test_open_door_task_skips_when_door_already_open(mocker):
    mocker.patch("tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_OPEN

    fake_door = FakeDoor()

    task = tasks.OpenDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    # Ensure "Opening door" is not logged.
    for call in mock_logger.call_args_list:
        args, _ = call
        assert "Opening door" not in args[0]
    assert task.is_executed


# Test for CloseDoorTask when door is open.
def test_close_door_task_executes_when_door_open(mocker):
    mocker.patch("tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_OPEN

    fake_door = FakeDoor()

    task = tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_any_call("Closing door")
    assert task.is_executed


# Test for CloseDoorTask when current time is before exec_time.
def test_close_door_task_does_not_execute_before_time(mocker):
    mocker.patch("tasks.timing.now", return_value=3.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_OPEN

    fake_door = FakeDoor()

    task = tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    mock_logger.assert_not_called()
    assert not task.is_executed


# Test for CloseDoorTask when door is already closed.
def test_close_door_task_skips_when_door_already_closed(mocker):
    mocker.patch("tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_CLOSED

    fake_door = FakeDoor()

    task = tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    for call in mock_logger.call_args_list:
        args, _ = call
        assert "Closing door" not in args[0]
    assert task.is_executed


# Test that a task doesn't execute twice.
def test_task_does_not_execute_twice(mocker):
    mocker.patch("tasks.timing.now", return_value=10.0)
    mock_logger = mocker.patch("tasks.logger.info")

    class FakeDoor:
        state = door.STATE_OPEN

    fake_door = FakeDoor()

    task = tasks.CloseDoorTask(exec_time=5.0, door=fake_door)
    task.execute()

    # Reset logger call history.
    mock_logger.reset_mock()
    task.execute()

    # No new logging should occur on second execution.
    mock_logger.assert_not_called()


def test_get_latest_task(mocker):
    open_task = tasks.OpenDoorTask(exec_time=5.0, door=None)
    close_task = tasks.CloseDoorTask(exec_time=10.0, door=None)

    tasks_list = [open_task, close_task]

    mocker.patch("tasks.timing.now", return_value=11.0)
    latest_task = tasks.get_latest_task(tasks_list)

    mocker.patch("tasks.timing.now", return_value=6.0)
    latest_task = tasks.get_latest_task(tasks_list)

    assert latest_task == open_task
