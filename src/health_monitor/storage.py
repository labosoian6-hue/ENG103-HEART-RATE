import os
import csv
from datetime import datetime

from dotenv import load_dotenv
import dropbox

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


def upload_to_dropbox():
    """
    Upload the local readings CSV to Dropbox, overwriting the previous
    copy, under a dated filename like /readings_2026-10-06.csv.
    """
    try:
        load_dotenv()

        app_key = os.getenv("DROPBOX_APP_KEY")
        app_secret = os.getenv("DROPBOX_APP_SECRET")
        refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

        dbx = dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret
        )

        file_path = os.path.join(
            config.LOCAL_DATA_DIR,
            config.LOCAL_READINGS_FILE
        )

        with open(file_path, "rb") as file:
            data = file.read()

        date = datetime.now().strftime("%Y-%m-%d")
        dropbox_path = f"/readings_{date}.csv"

        dbx.files_upload(
            data,
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )

        print(f"Successfully uploaded {dropbox_path} to Dropbox.")
        return True

    except Exception as error:
        print(f"Dropbox upload failed: {error}")
        return False

if __name__ == "__main__":
    from .mock_sensor import MockHeartRateSensor
    from .alerts import evaluate

    sensor = MockHeartRateSensor()

    reading1 = sensor.read_vitals()
    reading2 = sensor.read_vitals()

    save_reading_locally(reading1, evaluate(reading1))
    save_reading_locally(reading2, evaluate(reading2))

    print("Two fake readings saved locally.")

    upload_to_dropbox()
