import time

from .alerts import AlertState


class Blinker:
    def __init__(self, interval):
        self.interval = interval
        self.is_on = False
        self.last_toggle = time.monotonic()

    def update(self):
        current_time = time.monotonic()

        if current_time - self.last_toggle >= self.interval:
            self.is_on = not self.is_on
            self.last_toggle = current_time

        return self.is_on


class LEDController:
    def __init__(self, green_pin, red_pin):
        self.green_pin = green_pin
        self.red_pin = red_pin

        self.slow_blinker = Blinker(1.0)
        self.fast_blinker = Blinker(0.25)

        # Remember what each LED was last set to, so we only act on changes
        self._green_state = None
        self._red_state = None

    def set_green(self, state):
        if state != self._green_state:
            self._green_state = state
            # TODO (Pi): replace this print with a real GPIO write
            print(f"Green LED: {'ON' if state else 'OFF'}")

    def set_red(self, state):
        if state != self._red_state:
            self._red_state = state
            # TODO (Pi): replace this print with a real GPIO write
            print(f"Red LED: {'ON' if state else 'OFF'}")

    def update(self, alert_state):
        if alert_state == AlertState.OK:
            self.set_green(True)
            self.set_red(False)

        elif alert_state == AlertState.BPM_ABNORMAL:
            self.set_green(False)
            self.set_red(self.slow_blinker.update())

        elif alert_state == AlertState.SPO2_ABNORMAL:
            self.set_green(False)
            self.set_red(self.fast_blinker.update())

        elif alert_state == AlertState.BOTH_ABNORMAL:
            self.set_green(False)
            self.set_red(True)

        else:
            # No reading yet / unknown state: both off
            self.set_green(False)
            self.set_red(False)


if __name__ == "__main__":
    controller = LEDController(green_pin=17, red_pin=27)

    states_to_test = [
        AlertState.OK,
        AlertState.BPM_ABNORMAL,
        AlertState.SPO2_ABNORMAL,
        AlertState.BOTH_ABNORMAL,
    ]

    print("Testing LED controller, each state runs for 4 seconds...")
    print("Press Ctrl+C to stop early.")

    try:
        for state in states_to_test:
            print(f"\n--- Now testing: {state.value} ---")
            end_time = time.monotonic() + 4
            while time.monotonic() < end_time:
                controller.update(state)
                time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nTest stopped.")
