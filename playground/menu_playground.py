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

r = RotaryIRQ(pin_num_clk=18,
              pin_num_dt=19,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)

scale_intervals = mcp4725_musical_scales.get_intervals()

singe_select_menu = m.SingleSelectVerticalScrollMenu(
    'Scale', selected='chromatic', items=scale_intervals)

numerical_range_menu = m.NumericalValueRangeMenu(
    "CV Probability", selected_value=50, increment=5)

current_menu = numerical_range_menu


def button_action(pin, event) -> None:
    global selected_index, menu_start_index
    if event == Button.PRESSED:
        if current_menu is singe_select_menu:
            singe_select_menu.set_menu_start_index(0)
            singe_select_menu.set_highlighted_index(0)
            singe_select_menu.set_selected_index(val_new)
            r.set(value=0)
        elif current_menu is numerical_range_menu:
            numerical_range_menu.set_selected(val_new)
            r.set(value=numerical_range_menu.selected_value)
            numerical_range_menu.display_menu()


b = Button(20, internal_pullup=True, callback=button_action)

# Initial display
if current_menu is singe_select_menu:
    r.set(value=0)
    val_old = -1
    r.set(min_val=0, max_val=len(singe_select_menu.items) - 1)
    singe_select_menu.display_menu()
elif current_menu is numerical_range_menu:
    val_old = -1
    r.set(value=numerical_range_menu.selected_value)
    r.set(min_val=numerical_range_menu.start,
          max_val=numerical_range_menu.stop, incr=numerical_range_menu.increment)
    numerical_range_menu.display_menu()

# loop
while True:
    val_new = r.value()
    b.update()

    # only update display if the value has changed
    if val_old != val_new:
        val_old = val_new

        if current_menu is singe_select_menu:
            singe_select_menu.scroll(val_new)
            singe_select_menu.set_highlighted_index(val_new)
            singe_select_menu.display_menu()
        elif current_menu is numerical_range_menu:
            numerical_range_menu.scroll(val_new)
            numerical_range_menu.display_menu()
