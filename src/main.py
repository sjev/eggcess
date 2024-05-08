""" main module for coop_door """

import microcontroller

import asyncio
import time

import wifi
import gc
import timing
import logger


from door import Door

__version__ = "2.0.0"


DEVICE_NAME = "eggcess_2"
STATUS_TOPIC = f"/status/{DEVICE_NAME}"
COMMAND_TOPIC = f"/{DEVICE_NAME}/cmd"
STATE_TOPIC = f"/{DEVICE_NAME}/state"


T_START = time.time()

logger.info(f"*** system start  v{__version__}***")

door = Door()

led = door.stepper.pins[0]


class Params:
    """holds parameters"""

    name: str = DEVICE_NAME
    open_time: float | None = None
    close_time: float | None = None
    date: str | None = None


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


async def report_status(period_sec=5):
    """report status"""

    # Pre-initialize the message dictionary with static values
    msg = {
        "name": DEVICE_NAME,
        "door_state": door.state,  # assuming door.state is static, remove if it changes
    }

    network = wifi.radio.ap_info

    while True:

        # Flash LED
        led.value = 1
        await asyncio.sleep(0.01)
        led.value = 0

        # Update dynamic values
        utc_time = time.localtime()
        uptime = time.time() - T_START

        msg.update(
            {
                "ip": wifi.radio.ipv4_address,
                "uptime_h": round(uptime / 3600, 3),
                "mem_free": gc.mem_free(),
                "rssi": network.rssi,
                "date": Params.date,
                "time": f"{utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02}",
                "open": (
                    timing.hours2str(Params.open_time) if Params.open_time else None
                ),
                "close": (
                    timing.hours2str(Params.close_time) if Params.close_time else None
                ),
                "door_state": door.state,  # update door state in case it changes
            }
        )

        # Print status to console, to avoid ampy timeout
        print(msg)

        # collect garbage (patch memory leak)
        gc.collect()

        await asyncio.sleep(period_sec)


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

            if Params.open_time is None or Params.close_time is None:
                raise ValueError("Open or close time is not set.")

            # perform action and get sleep duration
            sleep_duration = door.automate(
                current_hours, Params.open_time, Params.close_time
            )
            sleep_hr = sleep_duration / 3600
            wake_time = timing.hours2str((current_hours + sleep_hr) % 24)

            logger.info(f"sleep_duration: {sleep_hr:.3f} hours till {wake_time}")

            # wait until next event
            await asyncio.sleep(sleep_duration)

        except ValueError as e:
            logger.warning(f"Exception in open_and_close: {type(e).__name__}: {e}")
            await asyncio.sleep(1)


async def main():
    """main coroutine"""

    coros = [
        report_status(),
        daily_coro(),
        open_and_close(),
    ]

    await asyncio.gather(*coros)

    # this should never be reached
    logger.warning("main ended ...")
    await asyncio.sleep(5)
    microcontroller.reset()


# ------------------run main------------------

asyncio.run(main())
