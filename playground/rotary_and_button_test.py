# Encoder moves and resets the value

import time
from rotary_irq_rp2 import RotaryIRQ
from mp_button import Button

r = RotaryIRQ(pin_num_clk=18,
              pin_num_dt=19,
              min_val=-100,
              max_val=100,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)


def button_action(pin, event):
    # set rotary value back to 0 when button is pressed
    if event == Button.PRESSED:
        r.set(value=0)


b = Button(20, internal_pullup=True, callback=button_action)

val_old = r.value()

while True:
    val_new = r.value()
    b.update()

    # only print if the value has changed
    if val_old != val_new:
        val_old = val_new
        print('result =', val_new)
