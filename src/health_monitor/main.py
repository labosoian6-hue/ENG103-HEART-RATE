import time
from datetime import datetime

from . import config
from .mock_sensor import MockHeartRateSensor
from .alerts import evaluate
from .led import LEDController
from .storage import save_reading_locally, upload_to_dropbox

UPLOAD_RETRY_SECONDS = 300  # wait 5 minutes between failed upload attempts


def main():
    sensor = MockHeartRateSensor()

    controller = LEDController(
        green_pin=config.LED_OK_PIN,
        red_pin=config.LED_ALERT_PIN
    )

    # No alert state until the first real reading
    alert_state = None

    last_read_time = 0

    # Don't upload at startup; the first upload happens when the date changes.
    # To test the upload, temporarily subtract a day:
    #   datetime.now().date() - timedelta(days=1)
    last_upload_date = datetime.now().date()
    last_upload_attempt = 0

    try:
        while True:
            # 1. Update LEDs every pass so blinking stays smooth
            controller.update(alert_state)

            # 2. Take a reading at the configured interval
            current_time = time.monotonic()

            if current_time - last_read_time >= config.READ_INTERVAL_SECONDS:
                latest_reading = sensor.read_vitals()
                alert_state = evaluate(latest_reading)

                print(
                    f"BPM: {latest_reading.bpm}, "
                    f"SpO2: {latest_reading.spo2}, "
                    f"Alert: {alert_state.value}"
                )

                save_reading_locally(latest_reading, alert_state)
                last_read_time = current_time

            # 3. Daily upload, retried at most every UPLOAD_RETRY_SECONDS
            today = datetime.now().date()

            if (
                today != last_upload_date
                and current_time - last_upload_attempt >= UPLOAD_RETRY_SECONDS
            ):
                last_upload_attempt = current_time

                if upload_to_dropbox():
                    last_upload_date = today

            # 4. Small delay to avoid using 100% CPU
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nHealth monitor stopped.")


if __name__ == "__main__":
    main()
