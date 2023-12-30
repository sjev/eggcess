# modified from https://github.com/IDWizard/uln2003  (c) IDWizard 2017
# MIT License.
from utime import sleep_us, sleep, ticks_ms

LOW = 0
HIGH = 1
FULL_ROTATION = FULL_ROTATION = 2048 / 4

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
    """Class for controlling a stepper motor with a ULN2003 controller"""

    def __init__(self, pins, delay=STEP_DELAY_US):
        self.mode = HALF_STEP
        self.pin1 = pins[0]
        self.pin2 = pins[1]
        self.pin3 = pins[2]
        self.pin4 = pins[3]
        self.delay = delay  # Recommend 10+ for FULL_STEP, 1 is OK for HALF_STEP

        # Initialize all to 0
        self.reset()

    def step(self, count, direction=1):
        """Rotate count steps. direction = -1 means backwards"""
        try:
            for _ in range(count):
                for bit in self.mode[::direction]:
                    self.pin1.value(bit[0])
                    self.pin2.value(bit[1])
                    self.pin3.value(bit[2])
                    self.pin4.value(bit[3])
                    sleep_us(self.delay)
        except Exception:
            print("Exception while stepping")
        finally:
            self.reset()

    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1.value(0)
        self.pin2.value(0)
        self.pin3.value(0)
        self.pin4.value(0)


if __name__ == "__main__":
    # test code
    from machine import Pin

    DRIVE_PINS = [Pin(p, Pin.OUT) for p in [2, 3, 4, 5]]
    stepper = Stepper(DRIVE_PINS)

    for direction in [1, -1]:
        print(f"direction: {direction}")
        t_start = ticks_ms()
        stepper.step(FULL_ROTATION, direction)
        t_end = ticks_ms()
        print(f"duration: {t_end - t_start} ms")
        sleep(1)
