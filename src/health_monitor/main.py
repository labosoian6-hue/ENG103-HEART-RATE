import time
from datetime import date

from . import config
from . import live
from .alerts import evaluate
from .button import Button
from .led import LEDController
from .storage import save_reading_locally, upload_to_dropbox

UPLOAD_RETRY_SECONDS = 300


def create_sensor():
    if config.USE_MOCK_SENSOR:
        from .mock_sensor import MockHeartRateSensor
        return MockHeartRateSensor()
    from .sensor import HeartRateSensor
    return HeartRateSensor()


def main():
    sensor = create_sensor()
    controller = LEDController(config.LED_OK_PIN, config.LED_ALERT_PIN)
    button = Button(config.BUTTON_PIN)

    alert_state = None
    latest_reading = None
    latest_state = None
    last_read = 0.0
    last_upload_day = None
    last_upload_try = 0.0

    print("Monitor running. Press the button to save a reading. Ctrl+C to stop.")
    try:
        while True:
            controller.update(alert_state)
            now = time.monotonic()

            if now - last_read >= config.READ_INTERVAL_SECONDS:
                reading = sensor.read_vitals()
                last_read = time.monotonic()
                if not reading.valid:
                    print("No valid reading, place your finger on the sensor")
                    alert_state = None
                    latest_reading = None
                    latest_state = None
                else:
                    alert_state = evaluate(reading)
                    latest_reading = reading
                    latest_state = alert_state
                    print(f"BPM: {reading.bpm}, SpO2: {reading.spo2}, Alert: {alert_state.name.lower()}")
                live.write_latest(latest_reading, latest_state)

            if button.was_pressed():
                if latest_reading is not None:
                    save_reading_locally(latest_reading, latest_state)
                    print(f"Saved: BPM {latest_reading.bpm}, SpO2 {latest_reading.spo2}")
                else:
                    print("Nothing to save, no valid reading yet")

            today = date.today()
            if today != last_upload_day and time.monotonic() - last_upload_try >= UPLOAD_RETRY_SECONDS:
                last_upload_try = time.monotonic()
                try:
                    upload_to_dropbox()
                    last_upload_day = today
                except Exception as e:
                    print(f"Dropbox upload failed, will retry: {e}")

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        controller.close()
        sensor.close()


if __name__ == "__main__":
    main()
