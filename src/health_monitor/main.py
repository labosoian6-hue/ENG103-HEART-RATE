"""
Personal Health and Wellbeing System - main program.

- Reads BPM and SpO2 from the MAX30102 (or the mock sensor on a laptop).
- Shows the alert state on two LEDs.
- Saves the latest valid reading to CSV when the button is pressed.
- Uploads the CSV to Dropbox once per day (retries if it fails).
"""

import time
from datetime import date

from . import config
from .alerts import evaluate
from .button import Button
from .led import LEDController
from .storage import save_reading_locally, upload_to_dropbox

UPLOAD_RETRY_SECONDS = 300  # wait 5 minutes between failed upload attempts


def create_sensor():
    """Pick the real or mock sensor depending on config."""
    if config.USE_MOCK_SENSOR:
        from .mock_sensor import MockHeartRateSensor
        return MockHeartRateSensor()

    from .sensor import HeartRateSensor
    return HeartRateSensor()


def main():
    sensor = create_sensor()
    controller = LEDController(config.LED_OK_PIN, config.LED_ALERT_PIN)
    button = Button(config.BUTTON_PIN)

    alert_state = None      # None = no valid reading, both LEDs off
    latest_reading = None   # last valid reading, saved when button pressed
    latest_state = None

    last_read_time = 0.0

    current_date = date.today()
    upload_pending = False
    next_upload_attempt = 0.0

    print("Health monitor started. Press the button to save a reading.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            now = time.monotonic()

            # 1. Keep LEDs updated every pass (needed for blinking).
            controller.update(alert_state)

            # 2. Take a new reading at the configured interval.
            if now - last_read_time >= config.READ_INTERVAL_SECONDS:
                last_read_time = now
                reading = sensor.read_vitals()

                if not reading.valid:
                    print("No valid reading, place your finger on the sensor")
                    alert_state = None
                    latest_reading = None
                    latest_state = None
                else:
                    alert_state = evaluate(reading)
                    latest_reading = reading
                    latest_state = alert_state
                    print(
                        f"BPM: {reading.bpm}, SpO2: {reading.spo2}, "
                        f"Alert: {alert_state.name.lower()}"
                    )

            # 3. Button: save the latest valid reading.
            if button.was_pressed():
                if latest_reading is None:
                    print("No valid reading to save, place your finger on the sensor")
                else:
                    save_reading_locally(latest_reading, latest_state)
                    print(
                        f"Saved: BPM {latest_reading.bpm}, "
                        f"SpO2 {latest_reading.spo2}"
                    )

            # 4. Daily Dropbox upload (when the date changes), with retries.
            today = date.today()
            if today != current_date:
                current_date = today
                upload_pending = True
                next_upload_attempt = 0.0

            if upload_pending and now >= next_upload_attempt:
                if upload_to_dropbox():
                    print("Dropbox upload done.")
                    upload_pending = False
                else:
                    print(f"Dropbox upload failed, retrying in {UPLOAD_RETRY_SECONDS} s.")
                    next_upload_attempt = now + UPLOAD_RETRY_SECONDS

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nHealth monitor stopped.")

    finally:
        controller.close()
        sensor.close()


if __name__ == "__main__":
    main()
