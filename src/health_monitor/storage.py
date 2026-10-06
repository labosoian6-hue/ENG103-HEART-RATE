import os
import csv
from datetime import datetime

from . import config


def ensure_data_dir():
    os.makedirs(config.LOCAL_DATA_DIR, exist_ok=True)


def save_reading_locally(reading, alert_state):
    ensure_data_dir()

    file_path = os.path.join(
        config.LOCAL_DATA_DIR,
        config.LOCAL_READINGS_FILE
    )

    file_exists = os.path.exists(file_path)

    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["timestamp", "bpm", "spo2", "alert_state"])

        writer.writerow([
            datetime.now().isoformat(),
            reading.bpm,
            reading.spo2,
            alert_state.value
        ])

if __name__ == "__main__":
    from .mock_sensor import MockHeartRateSensor
    from .alerts import evaluate

    sensor = MockHeartRateSensor()

    reading1 = sensor.read_vitals()
    reading2 = sensor.read_vitals()

    save_reading_locally(reading1, evaluate(reading1))
    save_reading_locally(reading2, evaluate(reading2))

    print("Two fake readings saved locally.")
