""" main module for coop_door """
import asyncio
import json
import time

import machine
import network
from umqtt.robust import MQTTClient


import timing
import logger
import my_secrets as secrets

from door import Door, STATE_CLOSED


DEVICE_NAME = "coop_door"
STATUS_TOPIC = "/status/coop_door"
COMMAND_TOPIC = "/coop_door/cmd"


T_START = time.time()

led = machine.Pin(
    2, machine.Pin.OUT
)  # use LED to indicate status. This is also one of drive pins

door = Door()


class Params:
    """holds parameters"""

    name: str = DEVICE_NAME
    open_time: float | None = None
    close_time: float | None = None
    date: str | None = None
    desired_state: str = STATE_CLOSED


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
        print("opening door by command")
        asyncio.create_task(door.open())
    elif command == "close":
        print("closing door by command")
        asyncio.create_task(door.close())


async def mqtt_listener(client):
    while True:
        client.check_msg()  # Check for new MQTT messages
        await asyncio.sleep(1)  # Pause briefly to avoid blocking


async def report_status(client, period_sec=5):
    """report status"""

    while True:
        try:
            # flash led
            led.value(1)
            await asyncio.sleep(0.01)
            led.value(0)

            wifi = network.WLAN(network.STA_IF)

            utc_time = time.localtime()

            uptime = time.time() - T_START

            msg = {
                "name": DEVICE_NAME,
                "ip": wifi.ifconfig()[0],
                "uptime_h": round(uptime / 3600, 3),
                "rssi": wifi.status("rssi"),
                "door_state": door.state,
                "date": Params.date,
                "time": f"{utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02}",
                "open": timing.hours2str(Params.open_time)
                if Params.open_time
                else None,
                "close": timing.hours2str(Params.close_time)
                if Params.close_time
                else None,
            }
            client.publish(STATUS_TOPIC, json.dumps(msg))

            await asyncio.sleep(period_sec)
        except Exception as e:
            print(f"Exception in report_status: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def update_timing():
    """update time and open and close times"""

    while True:
        try:
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
            logger.info("time updated")

            await asyncio.sleep(delay_hours * 3600)

        except AssertionError as e:
            print(f"Exception in update_timing: {type(e).__name__}: {e}")
            await asyncio.sleep(1)
        except timing.MaxRetriesExceeded as e:
            logger.error(f"{type(e).__name__}: {e}")
            await asyncio.sleep(3600)


async def open_and_close():
    """open and close the door based on schedule, sleeps until next event"""
    # TODO: check desired state on startup
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
                next_action = door.open
            elif open_time <= current_hours < close_time:
                # After open time and before close time
                sleep_duration = (close_time - current_hours) * 3600  # hours to seconds
                next_action = door.close
            else:
                # After close time, schedule for next open time (next day)
                sleep_duration = (
                    (24 - current_hours) + open_time
                ) * 3600  # hours to seconds
                next_action = door.open

            logger.info(
                f"sleep_duration: {sleep_duration/3600} hours, next_action: {next_action.__name__}"
            )

            # wait until next event
            await asyncio.sleep(sleep_duration)

            logger.info(f"performing {next_action.__name__}")
            await next_action()

        except (AssertionError, KeyError) as e:
            logger.warning(f"Exception in open_and_close: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def main():
    """main coroutine"""
    logger.info("starting main")
    mqtt_client = connect_mqtt(DEVICE_NAME)

    coros = [
        report_status(mqtt_client),
        mqtt_listener(mqtt_client),
        update_timing(),
        open_and_close(),
    ]

    await asyncio.gather(*coros)

    # this should never be reached
    logger.warning("main ended, rebooting")
    await asyncio.sleep(2)
    machine.reset()


# ------------------run main------------------

asyncio.run(main())
