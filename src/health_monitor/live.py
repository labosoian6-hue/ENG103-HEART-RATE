"""Writes the newest reading to data/latest.json so the dashboard can show it live."""
import json
import os
import time

from . import config


def _path():
    return os.path.join(config.LOCAL_DATA_DIR, "latest.json")


def write_latest(reading, alert_state):
    """reading / alert_state may be None when there is no valid reading."""
    valid = reading is not None
    data = {
        "time": time.time(),
        "valid": valid,
        "bpm": reading.bpm if valid else None,
        "spo2": reading.spo2 if valid else None,
        "state": alert_state.name.lower() if alert_state is not None else None,
    }
    os.makedirs(config.LOCAL_DATA_DIR, exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, _path())  # atomic: dashboard never reads half a file
