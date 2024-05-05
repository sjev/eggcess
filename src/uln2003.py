# modified from https://github.com/IDWizard/uln2003  (c) IDWizard 2017
# MIT License.

import time
import board
import digitalio
from microcontroller import delay_us

# Constants
LOW = False
HIGH = True
FULL_ROTATION = 512  # steps per rotation

STEP_DELAY_US = 950

HALF_STEP = [
    [LOW, LOW, LOW, HIGH],
    [LOW, LOW, HIGH, HIGH],
    [LOW, LOW, HIGH, LOW],
    [LOW, HIGH, HIGH, LOW],
    [LOW, HIGH, LOW, LOW],
    [HIGH, HIGH, LOW, LOW],
    [HIGH, LOW, LOW, LOW],
    [HIGH, LOW, LOW, HIGH],
]

FULL_STEP = [
    [HIGH, LOW, HIGH, LOW],
    [LOW, HIGH, HIGH, LOW],
    [LOW, HIGH, LOW, HIGH],
    [HIGH, LOW, LOW, HIGH],
]


class Stepper:
    def __init__(self, pins, delay=STEP_DELAY_US):
        self.mode = HALF_STEP
        self.pins = [digitalio.DigitalInOut(pin) for pin in pins]
        for pin in self.pins:
            pin.direction = digitalio.Direction.OUTPUT
        self.delay = delay
        self.reset()

    def step(self, count, direction=1):
        try:
            for _ in range(count):
                for bit in self.mode[::direction]:
                    for pin, value in zip(self.pins, bit):
                        pin.value = value
                    delay_us(self.delay)
        except Exception as e:
            print("Exception while stepping:", e)
        finally:
            self.reset()

    def reset(self):
        for pin in self.pins:
            pin.value = LOW


# ----------------- testing ----------------------------
def test() -> None:
    # Define pin connections
    DRIVE_PINS = [board.D2, board.D3, board.D4, board.D5]
    stepper = Stepper(DRIVE_PINS)

    for direction in [1, -1]:
        print(f"Direction: {direction}")
        t_start = time.monotonic()  # Get current time in seconds
        stepper.step(FULL_ROTATION, direction)
        t_end = time.monotonic()  # Get current time in seconds
        print(f"Duration: {(t_end - t_start):.2f} s")
        time.sleep(1)
