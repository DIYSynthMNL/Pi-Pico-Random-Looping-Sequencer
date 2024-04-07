"""
Pi Pico Random Looping Sequencer (with 128x64 px OLED screen)
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

TODO implement control voltage input to change variables
"""

import machine
import mcp4725
import mcp4725_musical_scales as sc
import random
import menu as m

# pins
sda = 16
scl = 17
clock_input_pin = 22

# i2c
i2c_channel = 0
i2c = machine.I2C(i2c_channel, sda=machine.Pin(sda), scl=machine.Pin(scl))
dac = mcp4725.MCP4725(i2c, mcp4725.BUS_ADDRESS[0])

# setup pins
clock_in = machine.Pin(clock_input_pin, machine.Pin.IN, machine.Pin.PULL_DOWN)

# sequencer variables
MAX_NUMBER_OF_STEPS = 16
MIN_NUMBER_OF_STEPS = 2
MAX_NUMBER_OF_OCTAVES = 5
MIN_NUMBER_OF_OCTAVES = 1
cv_sequence = []
current_step = 0
number_of_steps = 16  # user can edit from 1 to any
step_changed_on_clock_pulse = False
cv_probability_of_change = 100  # user can edit 0 to 100

# scales
scale_intervals = sc.get_intervals()
current_scale_interval = "chromatic"
current_12bit_scale = sc.get_scale_of_12_bit_values(
    scale_interval=current_scale_interval
)
intervals = sc.get_intervals()
number_of_octaves = 1

# menu
scale_menu = m.SingleSelectVerticalScrollMenu(
    "Scale", selected=current_scale_interval, items=scale_intervals
)

cv_prob_menu = m.NumericalValueRangeMenu(
    "CVProb", selected=cv_probability_of_change, increment=5
)

steps_menu = m.NumericalValueRangeMenu(
    "Steps",
    selected=number_of_steps,
    increment=1,
    min_val=MIN_NUMBER_OF_STEPS,
    max_val=MAX_NUMBER_OF_STEPS,
)

octaves_menu = m.NumericalValueRangeMenu(
    "Octaves",
    selected=number_of_octaves,
    increment=1,
    min_val=MIN_NUMBER_OF_OCTAVES,
    max_val=MAX_NUMBER_OF_OCTAVES,
)

submenus = [scale_menu, cv_prob_menu, steps_menu, octaves_menu]
m.set_submenus(submenu_list=submenus)


def handle_clock_pulse() -> None:
    global current_step, step_changed_on_clock_pulse, clock_in, number_of_steps
    if current_step < number_of_steps:
        if clock_in.value() == 0 and step_changed_on_clock_pulse == False:
            step_changed_on_clock_pulse = True
            change_step_cv()
            dac.write(cv_sequence[current_step])
            if current_step == 0:
                print(cv_sequence)
            print("Step: ", current_step)
            print(cv_sequence[current_step])
            current_step += 1
        if clock_in.value() == 1 and step_changed_on_clock_pulse == True:
            step_changed_on_clock_pulse = False
    else:
        current_step = 0


def change_step_cv() -> None:
    global cv_sequence, current_12bit_scale, cv_probability_of_change
    # get random index of scale chosen
    random_scale_index = random.randint(0, len(current_12bit_scale) - 1)
    # set cv from scale list
    if generate_boolean_with_probability(cv_probability_of_change):
        print("change cv")
        cv_sequence[current_step] = current_12bit_scale[random_scale_index]


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


# initialize sequencer
populate_sequence_with_default()
print("Current scale:", current_12bit_scale)
print("Sequence:", cv_sequence)


def update_sequencer_values() -> None:
    """
    Updates sequencer values such as:
        scale,
        cv probability,
        number of steps,
        number of octaves
    """
    global current_12bit_scale, cv_probability_of_change, number_of_steps, current_scale_interval, number_of_octaves
    print("update_sequencer_values")
    submenus = m.get_submenu_list()
    for submenu in submenus:
        if submenu.name is "Scale":
            if current_scale_interval != submenu.selected:
                current_scale_interval = submenu.selected
                print("Scale changed:", current_scale_interval)

        elif submenu.name is "CVProb":
            if cv_probability_of_change != submenu.selected:
                cv_probability_of_change = submenu.selected
                print("CV probability changed:", cv_probability_of_change)

        elif submenu.name is "Steps":
            if number_of_steps != submenu.selected:
                number_of_steps = submenu.selected
                print("Number of steps changed", number_of_steps)

        elif submenu.name is "Octaves":
            if number_of_octaves != submenu.selected:
                number_of_octaves = submenu.selected
                print("Number of octaves changed:", number_of_octaves)

    current_12bit_scale = sc.get_scale_of_12_bit_values(
        scale_interval=current_scale_interval, octaves=number_of_octaves
    )


# loop
while True:
    # todo implement analog input
    m.loop_main_menu(update_main_program_values_callback=update_sequencer_values)
    handle_clock_pulse()
