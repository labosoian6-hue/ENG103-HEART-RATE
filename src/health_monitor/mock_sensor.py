
import random
from dataclasses import dataclass


@dataclass
class Reading:
    bpm: float
    spo2: float
    valid: bool


class MockHeartRateSensor:
    def __init__(self, abnormal_chance: float = 0.15):
        self.abnormal_chance = abnormal_chance

    def read_vitals(self) -> Reading:
        if random.random() < self.abnormal_chance:
            # occasionally simulate something the alert logic should catch
            bpm = random.choice([random.uniform(30, 49), random.uniform(121, 160)])
            spo2 = random.uniform(85, 93)
        else:
            bpm = random.uniform(60, 100)
            spo2 = random.uniform(95, 100)
        return Reading(bpm=round(bpm, 1), spo2=round(spo2, 1), valid=True)

    def close(self):
        pass


if __name__ == "__main__":
    sensor = MockHeartRateSensor()
    for _ in range(5):
        r = sensor.read_vitals()
        print(f"BPM: {r.bpm}, SpO2: {r.spo2}%, valid: {r.valid}")
