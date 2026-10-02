"""
On-device tests, run from /test/ by `invoke hw-test`.

Results go to a file because the Wi-Fi test drops the web serial console.
"""

import os
import time

import microcontroller
import wifi

TEST_DIR = "/test"
RESULT_FILE = f"{TEST_DIR}/results.txt"
UNREACHABLE_BROKER = "192.168.1.254"
MAX_BLOCK_S = 30.0  # mqtt outage must not stall the main loop near the 300 s watchdog

_out = open(RESULT_FILE, "w")


def report(line: str) -> None:
    print(line)
    _out.write(line + "\n")
    _out.flush()


def feed_watchdog() -> None:
    # the watchdog set by main.py may still be armed in the REPL
    try:
        microcontroller.watchdog.feed()
    except Exception:  # pylint: disable=broad-except
        pass


def check(fn) -> None:
    feed_watchdog()
    try:
        info = fn()
        report(f"PASS {fn.__name__}" + (f": {info}" if info else ""))
    except Exception as e:  # pylint: disable=broad-except
        report(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")


def test_imports():
    # pylint: disable=import-outside-toplevel,unused-import
    import daily_tasks  # noqa: F401
    import door  # noqa: F401
    import logger  # noqa: F401
    import mqtt  # noqa: F401
    import sun  # noqa: F401
    import timing  # noqa: F401


def test_utc_offset():
    import timing  # pylint: disable=import-outside-toplevel

    assert timing.utc_offset((2026, 1, 15, 12)) == 1.0
    assert timing.utc_offset((2026, 7, 15, 12)) == 2.0
    assert timing._last_sunday(2026, 3) == 29  # pylint: disable=protected-access
    return f"now={timing.utc_offset(time.localtime())}"


def test_door_times():
    import daily_tasks  # pylint: disable=import-outside-toplevel
    import timing  # pylint: disable=import-outside-toplevel

    open_task = daily_tasks.OpenDoorTask(None, door=None)
    close_task = daily_tasks.CloseDoorTask(None, door=None)
    daily_tasks.UpdateDoorTimesTask(0.1, open_task, close_task).main()

    offset = timing.utc_offset(time.localtime())
    not_before_utc = float(os.getenv("NOT_BEFORE", "0.0")) - offset
    assert open_task.exec_time >= not_before_utc - 1e-6, open_task.exec_time
    # CircuitPython cannot join adjacent f-strings
    open_local = timing.hours2str(open_task.exec_time + offset)
    close_local = timing.hours2str(close_task.exec_time + offset)
    return f"open {open_local} local, close {close_local} local"


def test_ntp():
    import timing  # pylint: disable=import-outside-toplevel

    timing.update_ntp_time(max_attempts=2, retry_delay=1)
    assert timing.is_rtc_set()


def test_logger_bad_path():
    import logger  # pylint: disable=import-outside-toplevel

    logger.log_to_file("hw-test", file="/no_such_dir/log.txt")


def test_truncate_log():
    import logger  # pylint: disable=import-outside-toplevel

    path = f"{TEST_DIR}/trunc.txt"
    with open(path, "w") as f:
        for i in range(10):
            f.write(f"line {i}\n")
    logger.truncate_log(file=path, max_lines=5, keep_lines=2)
    with open(path) as f:
        assert f.read() == "line 8\nline 9\n"
    os.remove(path)


def test_mqtt_broker():
    import mqtt  # pylint: disable=import-outside-toplevel

    client = mqtt.get_client()
    link = mqtt.Connection(client)
    link.service(f"/{mqtt.DEVICE_NAME}/test", lambda: "hw-test")
    assert link._up, "not connected"  # pylint: disable=protected-access
    client.disconnect()


def test_mqtt_unreachable_does_not_block():
    import mqtt  # pylint: disable=import-outside-toplevel

    client = mqtt.get_client()
    client.broker = UNREACHABLE_BROKER
    link = mqtt.Connection(client)
    start = time.monotonic()
    link.service("/hw-test", lambda: "x")
    elapsed = time.monotonic() - start
    assert not link._up  # pylint: disable=protected-access
    assert elapsed < MAX_BLOCK_S, f"blocked {elapsed:.1f} s"
    return f"returned in {elapsed:.1f} s"


def test_wifi_reconnect():
    import mqtt  # pylint: disable=import-outside-toplevel

    wifi.radio.stop_station()
    assert not wifi.radio.connected, "still connected after stop"
    mqtt._ensure_wifi()  # pylint: disable=protected-access
    assert wifi.radio.connected, "not reconnected"
    return f"ip {wifi.radio.ipv4_address}"


report(f"START {time.localtime()}")
for test in [
    test_imports,
    test_utc_offset,
    test_door_times,
    test_ntp,
    test_logger_bad_path,
    test_truncate_log,
    test_mqtt_broker,
    test_mqtt_unreachable_does_not_block,
]:
    check(test)
report("WIFI_DROP")  # host stops reading the console and polls the results file
check(test_wifi_reconnect)
report("DONE")
_out.close()

if not wifi.radio.connected:
    # never leave the device offline: a reset restores production code and Wi-Fi
    microcontroller.reset()
