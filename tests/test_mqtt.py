from unittest.mock import Mock

import pytest

import mqtt


@pytest.fixture(autouse=True)
def quiet_logger(mocker):
    mocker.patch("mqtt.logger")
    mocker.patch("mqtt.wifi.radio.connected", True)


def test_connects_then_publishes_status():
    client = Mock()
    conn = mqtt.Connection(client)

    conn.service("/status", lambda: "ok")

    client.connect.assert_called_once()
    client.publish.assert_called_once_with("/status", "ok")


def test_broker_down_does_not_raise_and_waits_before_retry(mocker):
    clock = mocker.patch("mqtt.time.monotonic", return_value=100.0)
    client = Mock()
    client.connect.side_effect = OSError("ECONNREFUSED")
    conn = mqtt.Connection(client, retry_s=60.0)

    conn.service("/status", lambda: "ok")
    conn.service("/status", lambda: "ok")
    assert client.connect.call_count == 1

    clock.return_value = 161.0
    conn.service("/status", lambda: "ok")
    assert client.connect.call_count == 2


def test_lost_connection_reconnects_on_next_attempt(mocker):
    clock = mocker.patch("mqtt.time.monotonic", return_value=100.0)
    client = Mock()
    conn = mqtt.Connection(client, retry_s=60.0)
    conn.service("/status", lambda: "ok")

    client.loop.side_effect = OSError("ECONNRESET")
    conn.service("/status", lambda: "ok")

    client.loop.side_effect = None
    clock.return_value = 200.0
    conn.service("/status", lambda: "ok")

    assert client.connect.call_count == 2


def test_error_is_logged_once_per_outage(mocker):
    log = mocker.patch("mqtt.logger")
    clock = mocker.patch("mqtt.time.monotonic", return_value=0.0)
    client = Mock()
    client.connect.side_effect = OSError("down")
    conn = mqtt.Connection(client, retry_s=1.0)

    for t in range(5):
        clock.return_value = float(t * 2)
        conn.service("/status", lambda: "ok")

    assert log.error.call_count == 1


def test_reconnects_wifi_when_down(mocker):
    mocker.patch("mqtt.wifi.radio.connected", False)
    connect_wifi = mocker.patch("mqtt.wifi.radio.connect")

    mqtt.Connection(Mock()).service("/status", lambda: "ok")

    connect_wifi.assert_called_once()
