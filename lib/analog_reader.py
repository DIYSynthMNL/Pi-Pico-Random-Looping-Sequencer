"""
Analog reader from the Euro Pi
All credits go to Rory Allen 2024
https://github.com/Allen-Synthesis/EuroPi/blob/main/software/firmware/europi.py

"""

from machine import ADC
from machine import Pin

# Analogue voltage read range.
MIN_INPUT_VOLTAGE = -5
MAX_INPUT_VOLTAGE = 5
DEFAULT_SAMPLES = 32

# Standard max int consts.
MAX_UINT16 = 65535

# todo implement calibration script
INPUT_CALIBRATION_VALUES = [384, 44634]


def clamp(value, low, high):
    """Returns a value that is no lower than 'low' and no higher than 'high'."""
    return max(min(value, high), low)


class AnalogueReader:
    """A base class for common analogue read methods.

    This class in inherited by classes like Knob and AnalogueInput and does
    not need to be used by user scripts.
    """

    def __init__(self, pin, samples=DEFAULT_SAMPLES, deadzone=0.0):
        self.pin_id = pin
        self.pin = ADC(Pin(pin))
        self.set_samples(samples)
        self.set_deadzone(deadzone)

    def _sample_adc(self, samples=None):
        # Over-samples the ADC and returns the average.
        value = 0
        for _ in range(samples or self._samples):
            value += self.pin.read_u16()
        return round(value / (samples or self._samples))

    def set_samples(self, samples):
        """Override the default number of sample reads with the given value."""
        if not isinstance(samples, int):
            raise ValueError(f"set_samples expects an int value, got: {samples}")
        self._samples = samples

    def set_deadzone(self, deadzone):
        """Override the default deadzone with the given value."""
        if not isinstance(deadzone, float):
            raise ValueError(f"set_deadzone expects an float value, got: {deadzone}")
        self._deadzone = deadzone

    def percent(self, samples=None, deadzone=None):
        """Return the percentage of the component's current relative range."""
        dz = self._deadzone
        if deadzone is not None:
            dz = deadzone
        value = self._sample_adc(samples) / MAX_UINT16
        value = value * (1.0 + 2.0 * dz) - dz
        return clamp(value, 0.0, 1.0)

    def range(self, steps=100, samples=None, deadzone=None):
        """Return a value (upper bound excluded) chosen by the current voltage value."""
        if not isinstance(steps, int):
            raise ValueError(f"range expects an int value, got: {steps}")
        percent = self.percent(samples, deadzone)
        if int(percent) == 1:
            return steps - 1
        return int(percent * steps)

    def choice(self, values, samples=None, deadzone=None):
        """Return a value from a list chosen by the current voltage value."""
        if not isinstance(values, list):
            raise ValueError(f"choice expects a list, got: {values}")
        percent = self.percent(samples, deadzone)
        if percent == 1.0:
            return values[-1]
        return values[int(percent * len(values))]


class AnalogueInput(AnalogueReader):
    """A class for handling the reading of analogue control voltage.

    The analogue input allows you to 'read' CV from anywhere between 0 and 12V.

    It is protected for the entire Eurorack range, so don't worry about
    plugging in a bipolar source, it will simply be clipped to 0-12V.

    The functions all take an optional parameter of ``samples``, which will
    oversample the ADC and then take an average, which will take more time per
    reading, but will give you a statistically more accurate result. The
    default is 32, provides a balance of performance vs accuracy, but if you
    want to process at the maximum speed you can use as little as 1, and the
    processor won't bog down until you get way up into the thousands if you
    wan't incredibly accurate (but quite slow) readings.

    The percent function takes an optional parameter ``deadzone``. However this
    parameter is ignored and just present to be compatible with the percent
    function of the AnalogueReader and Knob classes
    """

    def __init__(
        self, pin, min_voltage=MIN_INPUT_VOLTAGE, max_voltage=MAX_INPUT_VOLTAGE
    ):
        super().__init__(pin)
        self.MIN_VOLTAGE = min_voltage
        self.MAX_VOLTAGE = max_voltage
        self._gradients = []
        for index, value in enumerate(INPUT_CALIBRATION_VALUES[:-1]):
            try:
                self._gradients.append(
                    1 / (INPUT_CALIBRATION_VALUES[index + 1] - value)
                )
            except ZeroDivisionError:
                raise Exception(
                    "The input calibration process did not complete properly. Please complete again with rack power turned on"
                )
        self._gradients.append(self._gradients[-1])

    def percent(self, samples=None, deadzone=None):
        """Current voltage as a relative percentage of the component's range."""
        # Determine the percent value from the max calibration value.
        reading = self._sample_adc(samples) - INPUT_CALIBRATION_VALUES[0]
        max_value = max(
            reading,
            INPUT_CALIBRATION_VALUES[-1] - INPUT_CALIBRATION_VALUES[0],
        )
        return max(reading / max_value, 0.0)

    def read_voltage(self, samples=None):
        raw_reading = self._sample_adc(samples)
        reading = raw_reading - INPUT_CALIBRATION_VALUES[0]
        max_value = max(
            reading,
            INPUT_CALIBRATION_VALUES[-1] - INPUT_CALIBRATION_VALUES[0],
        )
        percent = max(reading / max_value, 0.0)
        # low precision vs. high precision
        if len(self._gradients) == 2:
            cv = 10 * max(
                reading / (INPUT_CALIBRATION_VALUES[-1] - INPUT_CALIBRATION_VALUES[0]),
                0.0,
            )
        else:
            index = int(percent * (len(INPUT_CALIBRATION_VALUES) - 1))
            cv = index + (
                self._gradients[index] * (raw_reading - INPUT_CALIBRATION_VALUES[index])
            )
        return clamp(cv, self.MIN_VOLTAGE, self.MAX_VOLTAGE)
