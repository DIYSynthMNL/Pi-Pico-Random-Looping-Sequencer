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

import mcp4725_musical_scales
import menu as m


scale_intervals = mcp4725_musical_scales.get_intervals()

singe_select_menu = m.SingleSelectVerticalScrollMenu(
    'Scale', selected='chromatic', items=scale_intervals)

numerical_range_menu = m.NumericalValueRangeMenu(
    "CV Probability", selected_value=50, increment=5)

current_menu = singe_select_menu

# Initial display
if current_menu is singe_select_menu:
    singe_select_menu.start()
elif current_menu is numerical_range_menu:
    numerical_range_menu.start()

# loop
while True:
    if current_menu is singe_select_menu:
        singe_select_menu.update()
    elif current_menu is numerical_range_menu:
        numerical_range_menu.update()
