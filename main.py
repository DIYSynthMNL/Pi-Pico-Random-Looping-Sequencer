"""
Pi Pico Quantized Random Looping Sequencer (with 128x64 px OLED screen)
By DIYSynthMNL

Wiring:
OLED
OLED SDA to GP16
OLED SCL to GP17
OLED VCC to 3.3V (TODO test 5V)
OLED GND to GND

DAC
DAC SDA to GP16
DAC SCL to GP17
DAC VCC to 5V
DAC GND to GND

Encoder (no breakout board)
ROT Pin 1 to GP19
ROT Pin 2 to GND
ROT Pin 3 to GP18
SW Pin 1 to GND
SW Pin 2 to GP20

Analog inputs
A0 = GP26
A1 = GP27
A2 = GP28
A3 = GP29

TODO: implement control voltage input to change variables
TODO: Schematic
"""

import machine
import mcp4725
import mcp4725_musical_scales as sc
import random
import menu as m
import analog_reader as analog_reader
from analog_reader import AnalogueReader
import time

# pins
sda = 16
scl = 17
digital_input_pin = 21  # inverted
clock_input_pin = 22  # inverted
digital_output_pin = 23  # inverted
A0 = 26
A1 = 27
A2 = 28
A3 = 29

# i2c
i2c_channel = 0
i2c = machine.I2C(i2c_channel, sda=machine.Pin(sda), scl=machine.Pin(scl))
dac = mcp4725.MCP4725(i2c, mcp4725.BUS_ADDRESS[0])

# setup pins
clock_in = machine.Pin(clock_input_pin, machine.Pin.IN, machine.Pin.PULL_DOWN)
digital_in = machine.Pin(digital_input_pin, machine.Pin.IN, machine.Pin.PULL_DOWN)
digital_out = machine.Pin(
    digital_output_pin, machine.Pin.OUT, machine.Pin.PULL_DOWN, value=0
)

# sequencer variables
MAX_NUMBER_OF_STEPS = 16
MIN_NUMBER_OF_STEPS = 2
MAX_NUMBER_OF_OCTAVES = 5
MIN_NUMBER_OF_OCTAVES = 1
cv_sequence = []
trigger_sequence = []
tuning_cv_sequence = [
    816,
    1632,
    816,
    1632,
    816,
    1632,
    816,
    1632,
    816,
    1632,
    816,
    1632,
    816,
    1632,
    816,
    1632,
]
test_cv_sequence = []
current_step = 0
number_of_steps = 16  # user can edit from 1 to any
step_changed_on_clock_pulse = False
cv_probability_of_change = 0  # user can edit 0 to 100
trigger_probability_of_change = 0
trigger_length_percent = 50
previous_trigger_ticks = 0
previous_clock_ticks = 0
clock_ms = 0
is_cv_erase = False
is_test_cv_sequence = False
is_tuning_cv_sequence = False

# scales
scale_intervals = sc.get_intervals()
current_scale_interval = "major"
starting_note = 12  # start at the next octave to prevent low voltage output issues (the note 0 will not be in tune) refer to the mcp4725 1vOct table
number_of_octaves = 1
current_12bit_scale = sc.get_scale_of_12_bit_values(
    scale_interval=current_scale_interval,
    starting_note=starting_note,
    octaves=number_of_octaves,
)

# menu
main_menu = m.MainMenu()

scale_menu = m.SingleSelectVerticalScrollMenu(
    "Scale",
    button=main_menu.button,
    selected=current_scale_interval,
    items=scale_intervals,
)

cv_prob_menu = m.NumericalValueRangeMenu(
    "CVProb", button=main_menu.button, selected=cv_probability_of_change, increment=5
)

trig_prob_menu = m.NumericalValueRangeMenu(
    "TrigProb",
    button=main_menu.button,
    selected=trigger_probability_of_change,
    increment=5,
)

trig_length_ms_menu = m.NumericalValueRangeMenu(
    "TrgLngth%",
    button=main_menu.button,
    selected=trigger_length_percent,
    increment=10,
)

steps_menu = m.NumericalValueRangeMenu(
    "Steps",
    button=main_menu.button,
    selected=number_of_steps,
    increment=1,
    min_val=MIN_NUMBER_OF_STEPS,
    max_val=MAX_NUMBER_OF_STEPS,
)

octaves_menu = m.NumericalValueRangeMenu(
    "Octaves",
    button=main_menu.button,
    selected=number_of_octaves,
    increment=1,
    min_val=MIN_NUMBER_OF_OCTAVES,
    max_val=MAX_NUMBER_OF_OCTAVES,
)

starting_note_menu = m.NumericalValueRangeMenu(
    "Start note",
    button=main_menu.button,
    selected=0,
    increment=1,
    min_val=0,
    max_val=36,
)

cv_erase_toggle_menu = m.ToggleMenu(
    "CvErase", button=main_menu.button, value=is_cv_erase
)

test_cv_scale_toggle_menu = m.ToggleMenu(
    "TestScale", button=main_menu.button, value=is_test_cv_sequence
)

is_tuning_cv_scale_menu = m.ToggleMenu(
    "TuningScale", button=main_menu.button, value=is_tuning_cv_sequence
)

submenus = [
    scale_menu,
    cv_prob_menu,
    trig_prob_menu,
    steps_menu,
    octaves_menu,
    starting_note_menu,
    cv_erase_toggle_menu,
    test_cv_scale_toggle_menu,
    is_tuning_cv_scale_menu,
    trig_length_ms_menu,
]
main_menu.set_submenus(submenu_list=submenus)

# analog inputs
cv1 = AnalogueReader(A3)
cv2 = AnalogueReader(A2)
cv3 = AnalogueReader(A1)
cv4 = AnalogueReader(A0)


def handle_clock_pulse() -> None:
    global current_step, step_changed_on_clock_pulse, clock_in, number_of_steps, previous_clock_ticks, clock_ms, previous_trigger_ticks
    current_clock_ticks = time.ticks_ms()

    if current_step < number_of_steps:
        if clock_in.value() == 0 and step_changed_on_clock_pulse == False:
            # actual clock value high

            previous_clock_ticks = current_clock_ticks

            test_cv_sequence = get_test_sequence()  # update the test_cv_sequence

            step_changed_on_clock_pulse = True

            randomly_change_current_step_cv()
            randomly_change_step_trigger()

            if is_cv_erase:
                cv_sequence[current_step] = current_12bit_scale[0]

            # check which cv sequence to output
            if is_test_cv_sequence:
                # outputs a cv sequence that runs through the scale ascending
                dac.write(test_cv_sequence[current_step])
            elif is_tuning_cv_sequence:
                dac.write(tuning_cv_sequence[current_step])
            else:
                # output cv
                dac.write(cv_sequence[current_step])

            if current_step == 0:
                pass
                # print(cv_sequence)
            # print("Step: ", current_step)
            # print(cv_sequence[current_step])

            # output_trigger()
            trig_length_ms = (clock_ms * trigger_length_percent) / 100
            print("Trigger length ms:", trig_length_ms)

            current_step += 1
        if clock_in.value() == 1 and step_changed_on_clock_pulse == True:
            # actual clock value low
            step_changed_on_clock_pulse = False
            # calculate length of clock pulse
            clock_ms = time.ticks_diff(current_clock_ticks, previous_clock_ticks)
            print("Clock length ms:", clock_ms)
    else:
        current_step = 0


def randomly_change_current_step_cv() -> None:
    # get random index of scale chosen
    random_scale_index = random.randint(0, len(current_12bit_scale) - 1)
    # set cv from scale list
    if generate_boolean_with_probability(cv_probability_of_change):
        # print("change cv")
        cv_sequence[current_step] = current_12bit_scale[random_scale_index]


def randomly_change_step_trigger() -> None:
    global trigger_sequence
    trig_on_or_off = random.randint(0, 1)
    if generate_boolean_with_probability(trigger_probability_of_change):
        trigger_sequence[current_step] = trig_on_or_off


def output_trigger() -> None:
    global previous_trigger_ticks, clock_ms

    trig_length_ms = (clock_ms * trigger_length_percent) / 100
    print("Trigger length ms:", trig_length_ms)

    print("Trigger sequence:", trigger_sequence)

    current_ticks = time.ticks_ms()
    print("Output trigger:", not trigger_sequence[current_step])
    digital_out.value(not trigger_sequence[current_step])

    if time.ticks_diff(current_ticks, previous_trigger_ticks) >= trig_length_ms:
        print("Ticks diff:", time.ticks_diff(current_ticks, previous_trigger_ticks))
        previous_trigger_ticks = current_ticks
        if trigger_sequence[current_step] == 1:
            print("Turn off trigger")
            digital_out.value(1)


def generate_boolean_with_probability(probability: float) -> bool:
    """
    Returns True or False based on the given probability.

    :param probability: The probability of returning True, in the range [0, 100].
    :type probability: float
    :return: True with probability `probability`, False otherwise.
    :rtype: bool
    """
    if not 0 <= probability <= 100:
        raise ValueError("Probability must be between 0 and 100")

    return random.random() * 100 <= probability


def populate_sequence_with_default() -> None:
    global cv_sequence, current_12bit_scale, MAX_NUMBER_OF_STEPS
    for _ in range(0, MAX_NUMBER_OF_STEPS):
        cv_sequence.append(current_12bit_scale[0])
        trigger_sequence.append(1)


def get_test_sequence() -> list[int]:
    sequence = []
    while len(sequence) < MAX_NUMBER_OF_STEPS:
        for cv_value in current_12bit_scale:
            if len(sequence) < MAX_NUMBER_OF_STEPS:
                sequence.append(cv_value)
    # print(sequence)
    return sequence


def update_sequencer_values() -> None:
    """
    Once the submenu's value is changed (rotary button clicked) it should update the global varable changed
    Updates sequencer values such as:
        scale,
        cv probability,
        number of steps,
        number of octaves
    """
    global current_12bit_scale, cv_probability_of_change, trigger_probability_of_change, number_of_steps, current_scale_interval, number_of_octaves, starting_note, is_test_cv_sequence, test_cv_sequence, is_cv_erase, is_tuning_cv_sequence, trigger_length_percent
    print("update_sequencer_values")
    submenus = main_menu.get_submenu_list()
    for submenu in submenus:
        if submenu.name is scale_menu.name:
            if current_scale_interval != submenu.selected:
                current_scale_interval = submenu.selected
                print("Scale changed:", current_scale_interval)

        elif submenu.name is cv_prob_menu.name:
            if cv_probability_of_change != submenu.selected:
                cv_probability_of_change = submenu.selected
                print("CV probability changed:", cv_probability_of_change)

        elif submenu.name is trig_prob_menu.name:
            if trigger_probability_of_change != submenu.selected:
                trigger_probability_of_change = submenu.selected
                print("Trig probability changed:", trigger_probability_of_change)

        elif submenu.name is steps_menu.name:
            if number_of_steps != submenu.selected:
                number_of_steps = submenu.selected
                print("Number of steps changed", number_of_steps)

        elif submenu.name is octaves_menu.name:
            if number_of_octaves != submenu.selected:
                number_of_octaves = submenu.selected
                print("Number of octaves changed:", number_of_octaves)

        elif submenu.name is starting_note_menu.name:
            if starting_note != submenu.selected:
                starting_note = submenu.selected
                print("Starting note changed:", starting_note)

        elif submenu.name is cv_erase_toggle_menu.name:
            if is_cv_erase != submenu.value:
                is_cv_erase = submenu.value
                print("ToggleMenu changed:", submenu.value)

        elif submenu.name is test_cv_scale_toggle_menu.name:
            if is_test_cv_sequence != submenu.value:
                is_test_cv_sequence = submenu.value
                print("ToggleMenu changed:", submenu.value)

        elif submenu.name is is_tuning_cv_scale_menu.name:
            if is_tuning_cv_sequence != submenu.value:
                is_tuning_cv_sequence = submenu.value
                print("ToggleMenu changed:", submenu.value)

        elif submenu.name is trig_length_ms_menu.name:
            if trigger_length_percent != submenu.selected:
                trigger_length_percent = submenu.selected
                print("Trig length changed:", trigger_length_percent)

        else:
            pass
            # print("Error, menu to be updated does not exist!")

    current_12bit_scale = sc.get_scale_of_12_bit_values(
        starting_note=starting_note + 12,
        scale_interval=current_scale_interval,
        octaves=number_of_octaves,
    )


# initialize sequencer
test_cv_sequence = get_test_sequence()
populate_sequence_with_default()
print("Current scale:", current_12bit_scale)
print("Sequence:", cv_sequence)

# previous_cv1_value = 0

# loop
while True:
    # todo implement analog input
    # cv1_value = cv1.choice(list(range(0, 101, 5)), deadzone=0.1)

    # if previous_cv1_value != cv1_value:
    #     # cv1 changed
    #     cv_probability_of_change = cv1_value
    #     # cv_prob_menu.set_selected(cv_probability_of_change)
    #     # main_menu.initialize_main_menu()
    #     previous_cv1_value = cv1_value

    main_menu.loop_main_menu(
        update_main_program_values_callback=update_sequencer_values
    )
    handle_clock_pulse()
