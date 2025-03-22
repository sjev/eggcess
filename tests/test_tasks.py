import pytest
import time
from tasks import Task, TaskManager


def fake_time_struct(hour, minute, day=1):
    """Helper to build a fake time.struct_time"""
    return time.struct_time((2023, 1, day, hour, minute, 0, 0, 0, 0))


def test_task_should_execute_true(mocker):
    mocker.patch("time.localtime", return_value=fake_time_struct(10, 30))
    task = Task("test", lambda: "ok", hour=9, minute=0)
    assert task.should_execute() is True


def test_task_should_execute_false_same_day(mocker):
    mocker.patch("time.localtime", return_value=fake_time_struct(10, 30, day=2))
    task = Task("test", lambda: "ok", hour=9, minute=0)
    task.last_execution_day = 2
    assert task.should_execute() is False


def test_task_should_execute_false_wrong_time(mocker):
    mocker.patch("time.localtime", return_value=fake_time_struct(8, 59))
    task = Task("test", lambda: "ok", hour=9, minute=0)
    assert task.should_execute() is False


def test_task_execute_increments_count_and_sets_day(mocker):
    mock_fn = mocker.Mock()
    mocker.patch("time.localtime", return_value=fake_time_struct(11, 0, day=5))

    task = Task("run", mock_fn, hour=10, minute=0)
    task.execute()

    assert task.execution_count == 1
    assert task.last_execution_day == 5
    mock_fn.assert_called_once()


def test_task_manager_executes_scheduled_task(mocker):
    mock_fn = mocker.Mock()
    mocker.patch("time.localtime", return_value=fake_time_struct(12, 0, day=3))

    task = Task("tm_task", mock_fn, hour=11, minute=0)
    tm = TaskManager()
    tm.add_task(task)
    tm.execute()

    assert task.execution_count == 1
    mock_fn.assert_called_once()


def test_task_manager_skips_unscheduled_task(mocker):
    mock_fn = mocker.Mock()
    mocker.patch("time.localtime", return_value=fake_time_struct(7, 59, day=2))

    task = Task("too_early", mock_fn, hour=8, minute=0)
    tm = TaskManager()
    tm.add_task(task)
    tm.execute()

    assert task.execution_count == 0
    mock_fn.assert_not_called()


def test_task_manager_handles_exception(mocker, capsys):
    def boom():
        raise ValueError("fail")

    mocker.patch("time.localtime", return_value=fake_time_struct(15, 0, day=10))

    task = Task("failing", boom, hour=15, minute=0)
    tm = TaskManager()
    tm.add_task(task)
    tm.execute()

    out = capsys.readouterr().out
    assert "Error executing task failing: fail" in out
    assert task.execution_count == 0
