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

from ssd1306 import SSD1306_I2C
from rotary_irq_rp2 import RotaryIRQ
from mp_button import Button
from menu import Menu
from menu import SingleSelectVerticalScrollMenu

# Hardware I2C using I2C0
i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))

# Scan I2C for device(s), prints list of device address(es)
print(i2c.scan())

# 128x64 OLED Display
display = SSD1306_I2C(128, 64, i2c)

r = RotaryIRQ(pin_num_clk=18,
              pin_num_dt=19,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)

scale_intervals = mcp4725_musical_scales.get_intervals()

main_menu = Menu("Main menu", ['Single Select', 'Single Select', 'Scale'])
menu1 = Menu("Single Select", ['M1Item1', 'M1Item2',
             'M1Item3', 'M1Item4', 'M1Item5', 'M1Item6'])
menu2 = Menu("Single Select", ['M2Item1', 'M2Item2', 'M2Item3', 'M2Item4', 'M2Item5'])
menu3 = SingleSelectVerticalScrollMenu(name='Scale', selection='chromatic', items=scale_intervals)
current_menu = main_menu

selected_index = 0
menu_start_index = 0
item_index = 0
total_lines = 4
pixel_y_shift = 20


def button_action(pin, event) -> None:
    global selected_index, menu_start_index
    # set rotary value back to 0 when button is pressed
    if event == Button.PRESSED:
        change_menu()
        selected_index = 0
        menu_start_index = 0
        r.set(value=0)


def change_menu() -> None:
    global current_menu, main_menu, menu1, menu2, menu3
    if current_menu == main_menu:
        if selected_index == 0:
            current_menu = menu1
        elif selected_index == 1:
            current_menu = menu2
        elif selected_index == 2:
            current_menu = menu3
    else:
        current_menu = main_menu
    update_encoder_range()
    display_menu(current_menu.items, current_menu.name)


b = Button(20, internal_pullup=True, callback=button_action)

r.set(value=0)
val_old = -1


def display_menu(menu_items, name, line_height=10, spacer=2) -> None:
    # shift all item positions down to prevent clipping issues
    display.fill(0)
    display.text(name, 2, 4, 1)
    display.rect(0, 0, 128, 15, 1)
    for i in range(min(len(menu_items) - menu_start_index, total_lines)):
        item_index = menu_start_index + i
        if item_index == selected_index:
            display.fill_rect(0, ((i * (line_height+spacer))-1) +
                              pixel_y_shift, 128, line_height, 1)
            display.text(menu_items[item_index], 0,
                         (i * (line_height+spacer))+pixel_y_shift, 0)
        else:
            display.text(menu_items[item_index], 0,
                         (i * (line_height+spacer))+pixel_y_shift, 1)
    display.show()


def update_encoder_range() -> None:
    # Update min_val and max_val based on the number of menu items
    r.set(min_val=0, max_val=len(current_menu.items) - 1)


# Initial display
display_menu(current_menu.items, current_menu.name)
update_encoder_range()

# loop
while True:
    val_new = r.value()
    b.update()

    # only update display if the value has changed
    if val_old != val_new:
        val_old = val_new

        # scroll
        if val_new > menu_start_index + (total_lines-1):
            menu_start_index += 1
        if val_new < menu_start_index:
            menu_start_index -= 1

        selected_index = val_new
        display_menu(current_menu.items, current_menu.name)
