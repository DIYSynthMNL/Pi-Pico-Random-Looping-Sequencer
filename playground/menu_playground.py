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

submenus = [scale_menu, cv_prob_menu, steps_menu]

current_menu = scale_menu

m.set_submenus(submenu_list=submenus)
m.start()

while True:
    # TODO if submenus are changed, update submenus
    submenus = m.get_submenu_list()
    for submenu in submenus:
        name = submenu.name
        if name is 'Scale':
            scale_menu.selected = submenu.selected
        if name is 'CVProb':
            cv_prob_menu.selected_value = submenu.selected_value
        if name is 'Steps':
            steps_menu.selected_value = submenu.selected_value
        
        
    if not m.exit_main_menu_loop():
        if m.main_menu_started == False:
            m.start()
        else:
            m.update()
    else:
        m.edit_submenu()
