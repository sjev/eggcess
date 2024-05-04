""" main module for coop_door """

import asyncio
import json
import time

import machine
import network
import gc
from umqtt.robust import MQTTClient


import timing
import logger
import webserver
import my_secrets as secrets

from door import Door

__version__ = "1.1.2"


DEVICE_NAME = "eggcess"
STATUS_TOPIC = f"/status/{DEVICE_NAME}"
COMMAND_TOPIC = f"/{DEVICE_NAME}/cmd"
STATE_TOPIC = f"/{DEVICE_NAME}/state"


T_START = time.time()

logger.info(f"*** system start  v{__version__}***")


led = machine.Pin(
    2, machine.Pin.OUT
)  # use LED to indicate status. This is also one of drive pins

door = Door()
wdt = machine.WDT(timeout=300_000)  # 5 minutes (in milliseconds)


class Params:
    """holds parameters"""

    name: str = DEVICE_NAME
    open_time: float | None = None
    close_time: float | None = None
    date: str | None = None


def connect_mqtt(client_id: str):
    """Connects to the MQTT broker"""

    client = MQTTClient(
        client_id,
        secrets.MQTT_BROKER,
        user=secrets.MQTT_USER,
        password=secrets.MQTT_PASSWORD,
    )
    client.set_callback(command_callback)
    client.connect()
    client.subscribe(COMMAND_TOPIC)
    return client


def command_callback(topic, msg):  # pylint: disable=unused-argument
    print(f"Received command: {msg}")
    command = msg.decode()
    if command == "open":
        logger.info("opening by command")
        door.open()
    elif command == "close":
        logger.info("closing by command")
        door.close()
    else:
        print("invalid command")


async def mqtt_listener(client):
    while True:
        try:
            client.check_msg()  # Check for new MQTT messages
            await asyncio.sleep(1)  # Pause briefly to avoid blocking
        except Exception as e:
            logger.error(f"Exception in mqtt_listener: {type(e).__name__}: {e}")


async def report_status(client, period_sec=5):
    """report status"""

    # Pre-initialize the message dictionary with static values
    msg = {
        "name": DEVICE_NAME,
        "door_state": door.state,  # assuming door.state is static, remove if it changes
    }

    wifi = network.WLAN(network.STA_IF)

    while True:
        try:
            # Flash LED
            led.value(1)
            await asyncio.sleep(0.01)
            led.value(0)
            led.value(0)

            # Update dynamic values
            utc_time = time.localtime()
            uptime = time.time() - T_START

            msg.update(
                {
                    "ip": wifi.ifconfig()[0],
                    "uptime_h": round(uptime / 3600, 3),
                    "mem_free": gc.mem_free(),
                    "rssi": wifi.status("rssi"),
                    "date": Params.date,
                    "time": f"{utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02}",
                    "open": (
                        timing.hours2str(Params.open_time) if Params.open_time else None
                    ),
                    "close": (
                        timing.hours2str(Params.close_time)
                        if Params.close_time
                        else None
                    ),
                    "door_state": door.state,  # update door state in case it changes
                }
            )

            # Reset watchdog timer
            wdt.feed()

            # Optionally serialize and publish status
            json_status = json.dumps(msg)
            client.publish(STATUS_TOPIC, json_status)

            # Publish state
            client.publish(STATE_TOPIC, door.state)

            # Print status to console, to avoid ampy timeout
            print(msg)

            # collect garbage (patch memory leak)
            gc.collect()

            await asyncio.sleep(period_sec)
        except Exception as e:
            logger.error(f"Exception in report_status: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def report_status_min(period_sec=5):
    """minimal reporting, hopefully without memory leak"""

    wifi = network.WLAN(network.STA_IF)

    while True:
        try:
            # Flash LED
            led.value(1)
            await asyncio.sleep(0.01)
            led.value(0)

            # Print minimal status to console
            print(
                {
                    "mem_free": gc.mem_free(),
                    "rssi": wifi.status("rssi"),
                }
            )

            # Pause before next update
            await asyncio.sleep(period_sec)

        except Exception as e:
            logger.error(f"Exception in report_status: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def daily_coro():
    """update time and open and close times"""

    while True:
        try:
            # truncate log if necessary
            logger.truncate_log()

            # get open and close times
            date, hours = timing.now()
            Params.date = date
            Params.open_time, Params.close_time = timing.extract_floats_from_file(date)

            # update ntp time (may fail)
            print("updating time")
            timing.update_time()

            # schedule the next update, approx 1 am tomorrow
            delay_hours = 24 - hours + 1
            print(f"next update in {delay_hours} hours")
            logger.info(
                f"time updated, open: {timing.hours2str(Params.open_time)}, close: {timing.hours2str(Params.close_time)}"
            )

            # collect garbage
            gc.collect()

            await asyncio.sleep(delay_hours * 3600)

        except AssertionError as e:
            logger.warning(f"Exception in update_timing: {type(e).__name__}: {e}")
            await asyncio.sleep(1)
        except timing.MaxRetriesExceeded as e:
            logger.error(f"{type(e).__name__}: {e}")
            await asyncio.sleep(3600)


async def open_and_close():
    """open and close the door based on schedule, sleeps until next event"""

    await asyncio.sleep(5)  # wait for other coroutines to get open and close times

    while True:
        try:
            print("checking open and close times")
            # get current time
            _, current_hours = timing.now()

            # get open and close times
            open_time = Params.open_time
            close_time = Params.close_time

            assert open_time is not None, "open_time is None"
            assert close_time is not None, "close_time is None"

            # Calculate sleep duration until the next event
            if current_hours < open_time:
                # Before open time
                sleep_duration = (open_time - current_hours) * 3600  # hours to seconds
                action = door.close
                next_action = door.open

            elif open_time <= current_hours < close_time:
                # After open time and before close time
                sleep_duration = (close_time - current_hours) * 3600  # hours to seconds
                action = door.open
                next_action = door.close

            else:
                # After close time, schedule for next open time (next day)
                sleep_duration = (
                    (24 - current_hours) + open_time
                ) * 3600  # hours to seconds
                action = door.close
                next_action = door.open

            # execute current action, this sets correct state in case of restart
            print(f"Current: {door.state}, performing {action.__name__}")
            action()

            sleep_hr = sleep_duration / 3600
            wake_time = timing.hours2str((current_hours + sleep_hr) % 24)

            logger.info(
                f"sleep_duration: {sleep_hr:.3f} hours till {wake_time}, next_action: {next_action.__name__}"
            )

            # wait until next event
            await asyncio.sleep(sleep_duration)

            logger.info(f"performing {next_action.__name__}")
            next_action()

        except (AssertionError, KeyError) as e:
            logger.warning(f"Exception in open_and_close: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def main():
    """main coroutine"""

    mqtt_client = connect_mqtt(DEVICE_NAME)

    # start webserver
    tasks = []
    tasks.append(
        asyncio.create_task(asyncio.start_server(webserver.serve_client, "0.0.0.0", 80))
    )

    coros = [
        report_status(mqtt_client),
        # report_status_min(),
        mqtt_listener(mqtt_client),
        daily_coro(),
        open_and_close(),
    ]

    await asyncio.gather(*coros)

    # this should never be reached
    logger.warning("main ended, rebooting")
    await asyncio.sleep(2)
    machine.reset()


# ------------------run main------------------

asyncio.run(main())
