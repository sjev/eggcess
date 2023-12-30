""" class to manage the door """
from machine import Pin
import asyncio
import json

from timing import time_str
from uln2003 import Stepper, FULL_ROTATION


STATE_FILE = "door_state.json"

DRIVE_PINS = [Pin(p, Pin.OUT) for p in [2, 3, 4, 5]]


MM_PER_REV = 19.6  # mm travel per revolution of the motor
TRAVEL_MM = 340  # door travel distance in mm
OPEN_EXTRA_MM = 20  # extra mm to open door, push against mechanical stop


# door states
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_MOVING = "moving"
STATE_UNKNOWN = "unknown"

# door directions
DIRECTION_OPEN = -1
DIRECTION_CLOSE = 1


class State:
    """state of the door"""

    def __init__(self, name: str = STATE_UNKNOWN):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @classmethod
    def load(cls) -> "State":
        """read state from file"""
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                print(f"read state {data}")
                return State(data["state"])
        except OSError:
            return State(STATE_UNKNOWN)

    def save(self):
        """save state to file"""
        print(f"saving state {self.name}")
        data = {"state": self.name, "time": time_str()}
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)


def set_open():
    """set the door state to open"""
    state = State(STATE_OPEN)
    state.save()


def set_closed():
    """set the door state to closed"""
    state = State(STATE_CLOSED)
    state.save()


class Door:
    """door interface"""

    def __init__(self, auto_reset=True, save_state=True):
        self._stepper = Stepper(DRIVE_PINS)

        self._state = State.load()
        self._save_state = save_state  # save state to file?
        print(f"door state: {self._state}")

        if self.state in [STATE_UNKNOWN, STATE_MOVING]:
            # reset door
            if auto_reset:
                self.reset()

    @property
    def state(self) -> str:
        """return the current state"""
        return self._state.name

    @state.setter
    def state(self, state: str):
        """set the current state and save it to file"""
        self._state = State(state)
        if self._save_state:
            self._state.save()

    def reset(self):
        """fully open the door, aginst mechanical stop"""
        print("resetting door")
        self.open()

    async def move(self, direction: int, distance_mm: float):
        """move the door in the specified direction, provide feedback after each revolution"""
        # convert mm to revolutions
        revolutions = distance_mm / MM_PER_REV

        print(f"moving {direction} for {revolutions} revolutions")
        for _ in range(int(revolutions)):
            self._stepper.step(FULL_ROTATION, direction)
            print("revolutions: ", _ + 1)
            await asyncio.sleep(0.01)

        # remainder
        remainder = revolutions - int(revolutions)
        if remainder > 0:
            self._stepper.step(int(remainder * FULL_ROTATION), direction)
            print("remainder: ", remainder)

    async def open(self, distance_mm: float = TRAVEL_MM + OPEN_EXTRA_MM):
        """open the door"""
        print("opening door")
        if self.state == STATE_OPEN:
            print("door is already open")
            return

        self.state = STATE_MOVING
        await self.move(DIRECTION_OPEN, distance_mm)
        self.state = STATE_OPEN

    async def close(self, distance_mm: float = TRAVEL_MM):
        """close the door"""
        print("closing door")
        if self.state == STATE_CLOSED:
            print("door is already closed")
            return
        self.state = STATE_MOVING
        await self.move(DIRECTION_CLOSE, distance_mm)
        self.state = STATE_CLOSED


async def test():
    """test the door, import door and run door.test() in repl"""
    door = Door(save_state=False)
    distance_mm = 100

    await door.open(distance_mm)
    asyncio.sleep(2)
    await door.close(distance_mm)
    asyncio.sleep(2)


if __name__ == "__main__":
    print("testing door")
    asyncio.run(test())
