

from enum import Enum
from . import config


class AlertState(Enum):
    OK = "ok"
    BPM_ABNORMAL = "bpm_abnormal"
    SPO2_ABNORMAL = "spo2_abnormal"
    BOTH_ABNORMAL = "both_abnormal"


def evaluate(reading) -> AlertState:
    """
    reading: any object with .bpm and .spo2 attributes (works with
    both Reading from mock_sensor.py and the real sensor.py later).
    """
    bpm_bad = reading.bpm < config.BPM_LOW or reading.bpm > config.BPM_HIGH
    spo2_bad = reading.spo2 < config.SPO2_LOW

    if bpm_bad and spo2_bad:
        return AlertState.BOTH_ABNORMAL
    if bpm_bad:
        return AlertState.BPM_ABNORMAL
    if spo2_bad:
        return AlertState.SPO2_ABNORMAL
    return AlertState.OK

if __name__ == "__main__":
    from .mock_sensor import MockHeartRateSensor

    sensor = MockHeartRateSensor()
    for _ in range(10):
        reading = sensor.read_vitals()
        state = evaluate(reading)
        print(f"BPM: {reading.bpm}, SpO2: {reading.spo2}% -> {state.value}")
