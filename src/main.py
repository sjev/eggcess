"""

main module for coop_door


mqtt was difficult to get stable. On micropython door stops reacting after some time to commands.
On circuitpython connection errors are difficult to recover.



home assistant rest switch https://www.home-assistant.io/integrations/switch.rest/


"""

import gc
import time

import microcontroller
import wifi

import logger
import timing
from door import Door
import daily_tasks

__version__ = "2.1.0"


DEVICE_NAME = "eggcess_2"
STATUS_TOPIC = f"/status/{DEVICE_NAME}"
COMMAND_TOPIC = f"/{DEVICE_NAME}/cmd"
STATE_TOPIC = f"/{DEVICE_NAME}/state"


T_START = time.time()

logger.info(f"*** system start  v{__version__}***")

door = Door()
led = door.stepper.pins[0]
open_task = daily_tasks.OpenDoorTask(exec_time=None, door=door)


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


def report_status(p):
    """report status"""

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
            "ip": wifi.radio.ipv4_address,
            "uptime_h": round(uptime / 3600, 3),
            "mem_free": gc.mem_free(),
            "rssi": network.rssi,
            "date": Params.date,
            "time": f"{utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02}",
            "open": (timing.hours2str(Params.open_time) if Params.open_time else None),
            "close": (
                timing.hours2str(Params.close_time) if Params.close_time else None
            ),
            "door_state": door.state,  # update door state in case it changes
        }
    )

    # Print status to console, to avoid ampy timeout
    print(msg)


async def update_timing():
    """update time and open and close times"""

    try:
        # truncate log if necessary
        logger.truncate_log()

        # get open and close times
        date, hours = timing.time()
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

    except timing.MaxRetriesExceeded as e:
        logger.error(f"{type(e).__name__}: {e}")


def main():
    """main function"""

    logger.info("****** starting door ******")

    try:
        while True:
            pass

    except Exception as e:
        logger.error(f"Main crashed: {type(e).__name__}: {e}")

        time.sleep(5)
        microcontroller.reset()


if __name__ == "__main__":
    main()
