"""

main module for coop_door


mqtt was difficult to get stable. On micropython door stops reacting after some time to commands.
On circuitpython connection errors are difficult to recover.



home assistant rest switch https://www.home-assistant.io/integrations/switch.rest/


"""

import gc
import json
import os
import time

from microcontroller import watchdog as wdt
from watchdog import WatchDogMode
import wifi

import logger
import mqtt
import timing
from daily_tasks import CloseDoorTask, OpenDoorTask, SetClockTask, get_latest_task
from door import Door

__version__ = "2.3.2"


DEVICE_NAME = os.getenv("CIRCUITPY_WEB_INSTANCE_NAME", "eggcess")
STATUS_TOPIC = os.getenv("STATUS_TOPIC", f"/{DEVICE_NAME}/status")
STATE_TOPIC = os.getenv("STATE_TOPIC", f"/{DEVICE_NAME}/state")

# set time
timing.update_ntp_time()
T_START = time.time()

# show topics
logger.debug(f"{DEVICE_NAME=}")
logger.debug(f"{STATUS_TOPIC=}")
logger.debug(f"{STATE_TOPIC=}")

logger.info(f"*** system start  v{__version__}***")

# set watchdog
if wdt is None:
    raise RuntimeError("Watchdog not available")

wdt.timeout = 300  # 5 minutes
wdt.mode = WatchDogMode.RESET
wdt.feed()


door = Door()
led = door.stepper.pins[0]
open_task = OpenDoorTask(exec_time=None, door=door)
close_task = CloseDoorTask(exec_time=None, door=door)
set_clock_task = SetClockTask(exec_time=1.0)


def command_callback(client, topic, command):  # pylint: disable=unused-argument
    print(f"Received command: {command}")

    if command == "open":
        logger.info("opening by command")
        door.open()
    elif command == "close":
        logger.info("closing by command")
        door.close()
    else:
        print("invalid command")


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


def update_door_times():
    """update time and open and close times"""

    # check that clock is set
    if not timing.is_rtc_set():
        logger.error("RTC not set")
        raise RuntimeError("RTC not set")

    # get open and close times
    date = timing.date()

    open_time, close_time = timing.extract_floats_from_file(date)

    logger.info(
        f"{open_time=} ({timing.hours2str(open_time)}), {close_time=} ({timing.hours2str(close_time)})"
    )

    open_task.exec_time = open_time
    close_task.exec_time = close_time


def handle_mqtt(client):
    """perform mqtt tasks, blocking, delays main loop."""
    # check connection
    if not client.is_connected():
        try:
            client.connect()
        except Exception as e:
            logger.debug(f"MQTT connection failed: {type(e).__name__}: {e}")
            time.sleep(5)
            return

    client.loop(timeout=5.0)

    # send status
    client.publish(STATUS_TOPIC, status_msg())


def main():
    """main function"""

    update_door_times()

    tsk = get_latest_task([open_task, close_task])
    if tsk is not None:
        tsk.execute()

    mqtt_client = mqtt.get_client(on_message=command_callback)

    try:
        while True:
            handle_mqtt(mqtt_client)
            wdt.feed()
            # execute tasks
            set_clock_task.execute()
            open_task.execute()
            close_task.execute()

    except Exception as e:
        logger.error(f"Main crashed: {type(e).__name__}: {e}")

    logger.info("Main loop ended")


if __name__ == "__main__":
    main()
