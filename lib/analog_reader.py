"""
Python script from the EuroPi
This program is lisenced under the Apache License Version 2.0. (https://github.com/Allen-Synthesis/EuroPi/blob/main/software/LICENSE)
All credits go to Rory Allen 2024
https://github.com/Allen-Synthesis/EuroPi/blob/main/software/firmware/europi.py

Changes:
- Added invert to AnalogueReader
- Added map_value()

"""

from machine import ADC
from machine import Pin

# Analogue voltage read range.
MIN_INPUT_VOLTAGE = -5
MAX_INPUT_VOLTAGE = 5
DEFAULT_SAMPLES = 32

# Standard max int consts.
MAX_UINT16 = 65535


def clamp(value, low, high):
    """Returns a value that is no lower than 'low' and no higher than 'high'."""
    return max(min(value, high), low)


def map_value(value, in_low, in_high, out_low, out_high):
    """Returns a value that is mapped to two output values. Similar to the Arduino map() function."""
    return out_low + (out_high - out_low) * ((value - in_low) / (in_high - in_low))


def invert_value(value, max, min):
    return map_value(value, min, max, max, min)


class AnalogueReader:
    """A base class for common analogue read methods.

    This class in inherited by classes like Knob and AnalogueInput and does
    not need to be used by user scripts.
    """

    def __init__(self, pin, samples=DEFAULT_SAMPLES, deadzone=0.0, invert=True):
        self.pin_id = pin
        self.pin = ADC(Pin(pin))
        self.set_samples(samples)
        self.set_deadzone(deadzone)
        self.invert = invert

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
        if self.invert:
            return invert_value(clamp(value, 0.0, 1.0), 0.0, 1.0)
        else:
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
