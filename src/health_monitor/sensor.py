"""
Real MAX30102 sensor for the Raspberry Pi. It has the same read_vitals()
interface as MockHeartRateSensor, so main.py can use either one.

Driver: vrano714/max30102-tutorial-raspberrypi (max30102.py, hrcalc.py),
copied into this folder.
"""

from .mock_sensor import Reading


class HeartRateSensor:
    def __init__(self):
        # Import the driver here rather than at the top of the file, so
        # importing this module on a laptop without the driver doesn't crash.
        from . import max30102

        # Create the MAX30102 driver object
        self.sensor = max30102.MAX30102()

    def read_vitals(self) -> Reading:
        from . import hrcalc

        # Get red and IR sample lists from the MAX30102
        red, ir = self.sensor.read_sequential()

        # Calculate heart rate and SpO2
        hr, hr_valid, spo2, spo2_valid = hrcalc.calc_hr_and_spo2(ir, red)

        # Both measurements must be valid for the Reading to be valid
        valid = hr_valid and spo2_valid

        return Reading(
            bpm=round(hr),
            spo2=round(spo2),
            valid=valid
        )

    def close(self):
        # Shut the sensor down cleanly
        self.sensor.shutdown()
