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

scale_menu = m.SingleSelectVerticalScrollMenu(
    'Scale', selected='chromatic', items=scale_intervals)

cv_prob_menu = m.NumericalValueRangeMenu(
    "CVProb", selected_value=50, increment=5)

steps_menu = m.NumericalValueRangeMenu(
    "Steps", selected_value=1, increment=1, min_val=1, max_val=16)

current_menu = scale_menu

# # Initial display
# if current_menu is singe_select_menu:
#     singe_select_menu.start()
# elif current_menu is numerical_range_menu:
#     numerical_range_menu.start()

# # loop
# while True:
#     if current_menu is singe_select_menu:
#         singe_select_menu.update()
#     elif current_menu is numerical_range_menu:
#         numerical_range_menu.update()

m.set_submenus(submenu_list=[scale_menu, cv_prob_menu, steps_menu])
m.start()

while True:
    m.update()
