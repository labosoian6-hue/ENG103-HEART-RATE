"""
Push button with debounce.

Pi: reads the real button (GPIO pin to GND, internal pull-up).
Laptop: press Enter in the terminal to simulate a button press.
"""

import time

try:
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    import select
    import sys
    ON_PI = False


class Button:
    def __init__(self, pin, debounce=0.3):
        self.pin = pin
        self.debounce = debounce
        self._was_down = False
        self._last_press = 0.0

        if ON_PI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _is_down(self):
        if ON_PI:
            return GPIO.input(self.pin) == GPIO.LOW
        # Laptop: Enter key counts as one press.
        if select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            return True
        return False

    def was_pressed(self):
        """Returns True once per press. Call this every loop."""
        down = self._is_down()
        now = time.monotonic()

        pressed = (
            down
            and not self._was_down
            and now - self._last_press > self.debounce
        )

        if pressed:
            self._last_press = now
        self._was_down = down
        return pressed
