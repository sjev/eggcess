"""Manage the door for CircuitPython."""

import os
import board
import json

from timing import time_str
from uln2003 import Stepper, FULL_ROTATION
import logger

STATE_FILE = "door_state.json"

DRIVE_PINS = [board.D0, board.D1, board.D2, board.D3]  # type: ignore

MM_PER_REV = 19.6  # mm travel per revolution of the motor
TRAVEL_MM = int(os.getenv("TRAVEL_MM", "330"))  # door travel distance in mm
OPEN_EXTRA_MM = 10  # extra mm to open door, push against mechanical stop
EXTRA_DELAY = 5  # extra delay in seconds to ensure door state transition

logger.debug(f"Door travel distance: {TRAVEL_MM} mm")

# Door states
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_MOVING = "moving"
STATE_UNKNOWN = "unknown"

# Door directions
DIRECTION_OPEN = -1
DIRECTION_CLOSE = 1


class State:
    """Represents the door state."""

    def __init__(self, name: str = STATE_UNKNOWN):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @classmethod
    def load(cls) -> "State":
        """Load state from file."""
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                logger.debug(f"Loaded state: {data}")
                return cls(data.get("state", STATE_UNKNOWN))
        except OSError:
            logger.debug("Failed to load state, returning unknown state")
            return cls(STATE_UNKNOWN)

    def save(self):
        """Save state to file."""
        logger.debug(f"Saving state: {self.name}")
        data = {"state": self.name, "time": time_str()}
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)


class Door:
    """Door interface for open/close actions."""

    def __init__(self, auto_reset: bool = True):
        self.stepper = Stepper(DRIVE_PINS)
        self._state = State.load()
        logger.debug(f"Initial door state: {self._state}")

        if self.state in {STATE_UNKNOWN, STATE_MOVING} and auto_reset:
            logger.debug("Resetting door")
            self.open()

    @property
    def state(self) -> str:
        """Return the current door state."""
        return self._state.name

    @state.setter
    def state(self, new_state: str):
        """Set a new door state and save it if needed."""
        self._state = State(new_state)

    def save_state(self):
        """Save the current door state."""
        self._state.save()

    def move(self, direction: int, distance_mm: float):
        """Move the door in the specified direction with feedback after each revolution."""
        revolutions = distance_mm / MM_PER_REV
        logger.debug(
            f"Moving: distance_mm={distance_mm}, direction={direction}, revolutions={revolutions:.2f}"
        )

        full_revs = int(revolutions)
        for i in range(full_revs):
            self.stepper.step(FULL_ROTATION, direction)
            logger.debug(f"Completed revolution {i + 1}")

        remainder = revolutions - full_revs
        if remainder > 0:
            steps = int(remainder * FULL_ROTATION)
            self.stepper.step(steps, direction)
            logger.debug(f"Completed remainder: {remainder:.2f}")

    def open(self, distance_mm: float = TRAVEL_MM + OPEN_EXTRA_MM):
        """Open the door."""
        logger.debug("Attempting to open door")
        if self.state == STATE_OPEN:
            logger.debug("Door is already open")
            return

        self.state = STATE_MOVING
        self.move(DIRECTION_OPEN, distance_mm)
        self.state = STATE_OPEN
        logger.debug("Door is open")

    def close(self, distance_mm: float = TRAVEL_MM):
        """Close the door."""
        logger.debug("Attempting to close door")
        if self.state == STATE_CLOSED:
            logger.debug("Door is already closed")
            return

        self.state = STATE_MOVING
        self.move(DIRECTION_CLOSE, distance_mm)
        self.state = STATE_CLOSED
        logger.debug("Door is closed")


def test():
    """Test the door functionality."""

    logger.debug("********* Running door test *********")
    door = Door(auto_reset=False)
    door.state = STATE_UNKNOWN
    test_distance = 10

    door.open(test_distance)
    door.close(test_distance)
    door.save_state()


if __name__ == "__main__":
    test()
