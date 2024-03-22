"""
Generates 12Bit value lists of musical scales from starting note and scale intervals.
For use with the MCP4725 DAC

Scale algorithm from https://github.com/hmillerbakewell/musical-scales/tree/main
read more here: https://musical-scales.readthedocs.io/en/latest/musical_scales.html
"""

# To get a 12 bit value from a note number, it must be multiplied by 68
# the multiplier depends on the dac supply voltage (formula will be put here)
multiplier = 68

scale_intervals = {
    "acoustic": [2, 2, 2, 1, 2, 1, 2],
    "aeolian": [2, 1, 2, 2, 1, 2, 2],
    "algerian": [2, 1, 3, 1, 1, 3, 1, 2, 1, 2],
    "super locrian": [1, 2, 1, 2, 2, 2, 2],
    "augmented": [3, 1, 3, 1, 3, 1],
    "bebop dominant": [2, 2, 1, 2, 2, 1, 1, 1],
    "blues": [3, 2, 1, 1, 3, 2],
    "chromatic": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "dorian": [2, 1, 2, 2, 2, 1, 2],
    "double harmonic": [1, 3, 1, 2, 1, 3, 1],
    "enigmatic": [1, 3, 2, 2, 2, 1, 1],
    "flamenco": [1, 3, 1, 2, 1, 3, 1],
    "romani": [2, 1, 3, 1, 1, 2, 2],
    "half-diminished": [2, 1, 2, 1, 2, 2, 2],
    "harmonic major": [2, 2, 1, 2, 1, 3, 1],
    "harmonic minor": [2, 1, 2, 2, 1, 3, 1],
    "hijaroshi": [4, 2, 1, 4, 1],
    "hungarian minor": [2, 1, 3, 1, 1, 3, 1],
    "hungarian major": [3, 1, 2, 1, 2, 1, 2],
    "in": [1, 4, 2, 1, 4],
    "insen": [1, 4, 2, 3, 2],
    "ionian": [2, 2, 1, 2, 2, 2, 1],
    "iwato": [1, 4, 1, 4, 2],
    "locrian": [1, 2, 2, 1, 2, 2, 2],
    "lydian augmented": [2, 2, 2, 2, 1, 2, 1],
    "lydian": [2, 2, 2, 1, 2, 2, 1],
    "locrian major": [2, 2, 1, 1, 2, 2, 2],
    "pentatonic major": [2, 2, 3, 2, 3],
    "melodic minor ascending": [2, 1, 2, 2, 2, 2, 1],
    "melodic minor descending": [2, 1, 2, 2, 2, 2, 1],
    "pentatonic minor": [3, 2, 2, 3, 2],
    "mixolydian": [2, 2, 1, 2, 2, 1, 2],
    "neapolitan major": [1, 2, 2, 2, 2, 2, 1],
    "neapolitan minor": [1, 2, 2, 2, 1, 3, 1],
    "octatonic c-d": [2, 1, 2, 1, 2, 1, 2, 1],
    "octatonic c-c#": [1, 2, 1, 2, 1, 2, 1],
    "persian": [1, 3, 1, 1, 2, 3, 1],
    "phrygian dominant": [1, 3, 1, 2, 1, 2, 2],
    "phrygian": [1, 2, 2, 2, 1, 2, 2],
    "prometheus": [2, 2, 2, 3, 1, 2],
    "harmonics": [3, 1, 1, 2, 2, 3],
    "tritone": [1, 3, 2, 1, 3, 2],
    "two-semitone tritone": [1, 1, 4, 1, 1, 4],
    "ukranian dorian": [2, 1, 3, 1, 2, 1, 2],
    "whole-tone scale": [2, 2, 2, 2, 2, 2],
    "yo": [3, 2, 2, 3, 2]
}

scale_intervals["major"] = scale_intervals["ionian"]


def get_scale_of_note_numbers(starting_note: int = 0, scale_interval: str = "ionian", octaves: int = 1) -> list[int]:
    """Returns a sequence of note numbers from the starting note number.

    All credits go to musical_scales.py by Hector Miller-Bakewell.
    """
    if scale_interval not in scale_intervals:
        print('Scale selected not in dictionary')  # ! handle error
    notes = [starting_note]
    for octave in range(0, octaves):
        for interval in scale_intervals[scale_interval]:
            notes.append(notes[-1] + interval)
    return notes


def get_scale_of_12_bit_values(starting_note: int = 0, scale_interval: str = "ionian", octaves: int = 1) -> list[int]:
    """Returns a sequence of 12 bit values for the MCP4725 DAC

    All credits go to musical_scales.py by Hector Miller-Bakewell.
    """
    notes = get_scale_of_note_numbers(
        starting_note=starting_note, scale_interval=scale_interval, octaves=octaves)
    dac_scale = []
    for note_number in notes:
        dac_scale.append(note_number*multiplier)
    return dac_scale


def get_intervals() -> list[str]:
    """Returns a list of available scale intervals to choose from"""
    intervals_list = list(scale_intervals.keys())
    intervals_list.sort()
    return intervals_list


def test_print():
    print(get_scale_of_note_numbers(scale_interval="chromatic", octaves=1))
    print(get_scale_of_12_bit_values(scale_interval="chromatic", octaves=1))
