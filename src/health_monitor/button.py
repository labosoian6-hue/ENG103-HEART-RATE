"""
Push button with debounce.

Pi: a background event remembers presses, even while the sensor is being read.
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
        self._pressed = False
        self._was_down = False
        self._last_press = 0.0

        if ON_PI:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Runs in the background, so a press is not missed while the
            # main loop is busy reading the sensor.
            GPIO.add_event_detect(
                self.pin,
                GPIO.FALLING,
                callback=self._on_press,
                bouncetime=int(self.debounce * 1000),
            )

    def _on_press(self, channel):
        self._pressed = True

    def was_pressed(self):
        """Returns True once per press. Call this every loop."""
        if ON_PI:
            if self._pressed:
                self._pressed = False
                return True
            return False

        # Laptop: Enter key counts as one press.
        down = False
        if select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            down = True

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
