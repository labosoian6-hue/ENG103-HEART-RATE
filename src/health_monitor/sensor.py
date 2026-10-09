"""
MAX30102 heart rate / SpO2 sensor with noise filtering.

Each raw reading is checked against a believable range, then the median of
the last few good readings is returned so one bad reading can't change the result.
"""

from collections import deque
from statistics import median

from .mock_sensor import Reading

# Plausible resting ranges. Anything outside is treated as noise.
BPM_MIN, BPM_MAX = 40, 180
SPO2_MIN, SPO2_MAX = 85, 100

WINDOW_SIZE = 5        # how many good readings the median uses
MIN_READINGS = 3       # need this many good readings before reporting
MAX_BAD_IN_ROW = 3     # this many bad reads in a row = finger removed


class HeartRateSensor:
    def __init__(self):
        # Import the driver here so a laptop without the sensor libraries
        # doesn't crash just by importing this file.
        from .max30102 import MAX30102
        from . import hrcalc

        self.hrcalc = hrcalc
        self.sensor = MAX30102()

        self.bpm_history = deque(maxlen=WINDOW_SIZE)
        self.spo2_history = deque(maxlen=WINDOW_SIZE)
        self.bad_in_row = 0

    def _reset_history(self):
        self.bpm_history.clear()
        self.spo2_history.clear()

    def read_vitals(self):
        red, ir = self.sensor.read_sequential()
        hr, hr_valid, spo2, spo2_valid = self.hrcalc.calc_hr_and_spo2(ir, red)

        good = (
            hr_valid
            and spo2_valid
            and BPM_MIN <= hr <= BPM_MAX
            and SPO2_MIN <= spo2 <= SPO2_MAX
        )

        if not good:
            self.bad_in_row += 1
            # Several bad reads in a row: finger probably removed, so forget
            # old values so they don't mix into the next measurement.
            if self.bad_in_row >= MAX_BAD_IN_ROW:
                self._reset_history()
            return Reading(bpm=0, spo2=0, valid=False)

        self.bad_in_row = 0
        self.bpm_history.append(hr)
        self.spo2_history.append(spo2)

        # Not enough good readings yet to trust the result.
        if len(self.bpm_history) < MIN_READINGS:
            return Reading(bpm=0, spo2=0, valid=False)

        return Reading(
            bpm=round(median(self.bpm_history)),
            spo2=round(median(self.spo2_history)),
            valid=True,
        )

    def close(self):
        self.sensor.shutdown()
