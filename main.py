import machine
import mcp4725
import mcp4725_musical_scales as sc
import random

# pins
sda = 16
scl = 17
clock_input_pin = 22

# i2c
i2c_channel = 0
i2c = machine.I2C(i2c_channel, sda=machine.Pin(sda), scl=machine.Pin(scl))
dac = mcp4725.MCP4725(i2c, mcp4725.BUS_ADDRESS[0])

# setup pins
clock_in = machine.Pin(clock_input_pin, machine.Pin.OUT, machine.Pin.PULL_DOWN)

# sequencer variables
cv_sequence = []
current_step = 0
number_of_steps = 16  # ! user can edit from 1 to any
step_changed_on_clock_pulse = False
cv_probability_of_change = 100  # ! user can edit 0 to 100

# scales
current_scale = sc.get_scale_of_12_bit_values()
intervals = sc.get_intervals()


def handle_clock_pulse() -> None:
    global current_step, step_changed_on_clock_pulse, clock_in, number_of_steps
    if current_step < number_of_steps-1:
        if clock_in.value() == 0 and step_changed_on_clock_pulse == False:
            step_changed_on_clock_pulse = True
            change_step_cv()
            # cv output
            if current_step == 0:
                print(cv_sequence)
            print('Step: ', current_step)
            print(cv_sequence[current_step])
            current_step += 1
        if clock_in.value() == 1 and step_changed_on_clock_pulse == True:
            step_changed_on_clock_pulse = False
    else:
        current_step = 0


def change_step_cv() -> None:
    global cv_sequence, current_scale, cv_probability_of_change
    # get random index of scale chosen
    random_scale_index = random.randint(0, len(current_scale)-1)
    # set cv from scale list
    if generate_boolean_with_probability(cv_probability_of_change):
        print("change cv")
        cv_sequence[current_step] = current_scale[random_scale_index]


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
    global cv_sequence, current_scale, number_of_steps
    for _ in range(0, number_of_steps-1):
        cv_sequence.append(current_scale[0])


# initialize sequencer
populate_sequence_with_default()
print('Current scale:', current_scale)
print('Sequence:', cv_sequence)


# loop
while True:
    handle_clock_pulse()
