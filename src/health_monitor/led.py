"""
LED controller for the health monitor.

Works on:
- Raspberry Pi: controls real GPIO LEDs.
- Laptop: simulates LED changes with print statements.

LED meaning (2 LEDs, 4 states):
    OK             -> green solid
    BPM_ABNORMAL   -> red slow blink
    SPO2_ABNORMAL  -> red fast blink
    BOTH_ABNORMAL  -> red solid
    None           -> both off (no valid reading)
"""

import time

from .alerts import AlertState

try:
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    ON_PI = False


class Blinker:
    """Non-blocking blink timer: is_on() flips every `interval` seconds."""

    def __init__(self, interval):
        self.interval = interval
        self.start = time.monotonic()

    def is_on(self):
        elapsed = time.monotonic() - self.start
        return int(elapsed / self.interval) % 2 == 0


slow_blinker = Blinker(1.0)
fast_blinker = Blinker(0.25)


class LEDController:
    def __init__(self, green_pin, red_pin):
        self.green_pin = green_pin
        self.red_pin = red_pin

        # Remember the current LED states.
        self.green_state = False
        self.red_state = False

        if ON_PI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.green_pin, GPIO.OUT)
            GPIO.setup(self.red_pin, GPIO.OUT)
            GPIO.output(self.green_pin, GPIO.LOW)
            GPIO.output(self.red_pin, GPIO.LOW)

    def set_green(self, state):
        # Only do something when the state actually changes.
        if state != self.green_state:
            self.green_state = state

            if ON_PI:
                GPIO.output(self.green_pin, GPIO.HIGH if state else GPIO.LOW)
            else:
                print(f"Green LED: {'ON' if state else 'OFF'}")

    def set_red(self, state):
        # Only do something when the state actually changes.
        if state != self.red_state:
            self.red_state = state

            if ON_PI:
                GPIO.output(self.red_pin, GPIO.HIGH if state else GPIO.LOW)
            else:
                print(f"Red LED: {'ON' if state else 'OFF'}")

    def update(self, alert_state):
        """Set both LEDs for the current alert state. Call this every loop."""
        if alert_state is None:
            self.set_green(False)
            self.set_red(False)

        elif alert_state == AlertState.OK:
            self.set_green(True)
            self.set_red(False)

        elif alert_state == AlertState.BPM_ABNORMAL:
            self.set_green(False)
            self.set_red(slow_blinker.is_on())

        elif alert_state == AlertState.SPO2_ABNORMAL:
            self.set_green(False)
            self.set_red(fast_blinker.is_on())

        elif alert_state == AlertState.BOTH_ABNORMAL:
            self.set_green(False)
            self.set_red(True)

    def close(self):
        """Turn both LEDs off and release the GPIO pins."""
        self.set_green(False)
        self.set_red(False)
        if ON_PI:
            GPIO.cleanup()
