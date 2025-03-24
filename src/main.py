"""

main module for coop_door

"""

import gc
import json
import os
import time

import microcontroller
from microcontroller import watchdog as wdt
from watchdog import WatchDogMode, WatchDogTimeout
import wifi

import logger
import mqtt
import timing
from daily_tasks import (
    CloseDoorTask,
    OpenDoorTask,
    SetClockTask,
    UpdateDoorTimesTask,
    init_open_close,
)
from door import Door

__version__ = "3.2.1"


DEVICE_NAME = os.getenv("CIRCUITPY_WEB_INSTANCE_NAME", "eggcess")
STATUS_TOPIC = os.getenv("STATUS_TOPIC", f"/{DEVICE_NAME}/status")
STATE_TOPIC = os.getenv("STATE_TOPIC", f"/{DEVICE_NAME}/state")

# set time
timing.update_ntp_time()

# check that clock is set
if not timing.is_rtc_set():
    logger.error("RTC not set")
    raise RuntimeError("RTC not set")


T_START = time.time()

# show topics
logger.debug(f"{DEVICE_NAME=}")
logger.debug(f"{STATUS_TOPIC=}")
logger.debug(f"{STATE_TOPIC=}")

logger.info(f"*** system start  v{__version__}***")

# set watchdog
if wdt is None:
    raise RuntimeError("Watchdog not available")

try:
    wdt.timeout = 300.0  # 5 minutes
    wdt.mode = WatchDogMode.RAISE
    wdt.feed()
except Exception as e:
    logger.error(f"Could not init watchdog: {e}")


door = Door()
led = door.stepper.pins[0]


# create tasks
open_task = OpenDoorTask(exec_time=None, door=door)
close_task = CloseDoorTask(exec_time=None, door=door)
set_clock_task = SetClockTask(exec_time=1.0)
set_door_timing_task = UpdateDoorTimesTask(0.1, open_task, close_task)

all_tasks = [open_task, close_task, set_clock_task, set_door_timing_task]


def command_callback(client, topic, command):  # pylint: disable=unused-argument
    print(f"Received command: {command}")

    if command == "open":
        logger.info("opening by command")
        door.open()
    elif command == "close":
        logger.info("closing by command")
        door.close()
    elif command == "reset":
        logger.info("resetting by command")
        microcontroller.reset()
    else:
        logger.error(f"invalid command {command}")


def status_msg() -> str:
    """generate status string"""

    # Pre-initialize the message dictionary with static values
    msg = {
        "name": DEVICE_NAME,
        "door_state": door.state,  # assuming door.state is static, remove if it changes
    }

    network = wifi.radio.ap_info

    # Flash LED
    led.value = 1
    time.sleep(0.01)
    led.value = 0

    # Update dynamic values
    utc_time = time.localtime()
    uptime = time.time() - T_START

    msg.update(
        {
            "ip": str(wifi.radio.ipv4_address),
            "uptime_h": round(uptime / 3600, 3),  # type: ignore
            "mem_free": gc.mem_free(),  # type: ignore
            "rssi": network.rssi,  # type: ignore
            "date": timing.date(),
            "time": f"{utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02}",
            "open": (
                timing.hours2str(open_task.exec_time) if open_task.exec_time else "None"
            ),
            "close": (
                timing.hours2str(close_task.exec_time)
                if close_task.exec_time
                else "None"
            ),
            "door_state": door.state,  # update door state in case it changes
        }
    )
    status = json.dumps(msg)
    logger.debug(f"status: {status}")
    return status


def handle_mqtt(client):
    """Perform MQTT tasks, with graceful error handling."""
    try:
        # Check connection; try to connect if not connected.
        if not client.is_connected():
            try:
                client.connect()
            except Exception as e:
                logger.debug(f"MQTT connection failed: {type(e).__name__}: {e}")
                time.sleep(5)
                return

        # Run the MQTT loop and publish the status.
        client.loop(timeout=5.0)
        client.publish(STATUS_TOPIC, status_msg())

    except Exception as e:
        logger.debug(f"MQTT error occurred: {type(e).__name__}: {e}")
        # Try to disconnect gracefully.
        try:
            client.disconnect()
        except Exception as disconnect_error:
            logger.debug(
                f"Error during disconnect: {type(disconnect_error).__name__}: {disconnect_error}"
            )
        # Wait a few seconds before attempting to reconnect.
        time.sleep(5)
        try:
            client.connect()
        except Exception as connect_error:
            logger.debug(
                f"Reconnection attempt failed: {type(connect_error).__name__}: {connect_error}"
            )


def main():
    """main function"""

    set_door_timing_task.execute()

    init_open_close(open_task, close_task)

    mqtt_client = mqtt.get_client(on_message=command_callback)

    try:
        while True:
            handle_mqtt(mqtt_client)
            wdt.feed()
            # execute tasks
            for task in all_tasks:
                task.execute()

    except WatchDogTimeout:
        logger.error("Watchdog timeout")
        microcontroller.reset()

    except Exception as e:
        logger.error(f"Main crashed: {type(e).__name__}: {e}")

    logger.info("Main loop ended, resetting in 10 seconds")
    time.sleep(10)
    microcontroller.reset()


if __name__ == "__main__":
    main()
