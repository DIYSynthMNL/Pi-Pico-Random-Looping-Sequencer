"""
Menu Playground

Wiring:
OLED
OLED SDA to GP16
OLED SCL to GP17
OLED VCC to 3.3V or 5V (VBUS)
OLED GND to GND

Encoder (no breakout board)
ROT Pin 1 to GP19
ROT Pin 2 to GND
ROT Pin 3 to GP18
SW Pin 1 to GND
SW Pin 2 to GP20
"""

import machine
import mcp4725_musical_scales
import menu as m

from rotary_irq_rp2 import RotaryIRQ
from mp_button import Button
from menu import Menu

r = RotaryIRQ(pin_num_clk=18,
              pin_num_dt=19,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)

scale_intervals = mcp4725_musical_scales.get_intervals()

menu = m.SingleSelectVerticalScrollMenu(
    name='Scale', selection='chromatic', items=scale_intervals)
current_menu = menu


def button_action(pin, event) -> None:
    global selected_index, menu_start_index
    # set rotary value back to 0 when button is pressed
    if event == Button.PRESSED:
        current_menu.set_menu_start_index(0)
        current_menu.set_selected_index(0)
        r.set(value=0)


b = Button(20, internal_pullup=True, callback=button_action)

r.set(value=0)
val_old = -1


def update_encoder_range() -> None:
    # Update min_val and max_val based on the number of menu items
    r.set(min_val=0, max_val=len(current_menu.items) - 1)


# Initial display
menu.display_menu()
update_encoder_range()

# loop
while True:
    val_new = r.value()
    b.update()

    # only update display if the value has changed
    if val_old != val_new:
        val_old = val_new

        # scroll
        current_menu.scroll(val_new)
        # set selected index
        current_menu.set_selected_index(val_new) 
        # display menu
        current_menu.display_menu()
