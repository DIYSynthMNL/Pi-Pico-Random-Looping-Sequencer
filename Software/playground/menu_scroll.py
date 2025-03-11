"""
Menu Scroll

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
from ssd1306 import SSD1306_I2C
from rotary_irq_rp2 import RotaryIRQ
from mp_button import Button

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

menu_items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5",
              "Item 6", "Item 7", "Item 8", "Item 9", "Item 10"]
selected_index = 0
menu_start_index = 0
item_index = 0
total_lines = 5


def button_action(pin, event):
    global selected_index, menu_start_index
    # set rotary value back to 0 when button is pressed
    if event == Button.PRESSED:
        selected_index = 0
        menu_start_index = 0
        r.set(value=0)


b = Button(20, internal_pullup=True, callback=button_action)

r.set(value=0)
val_old = -1


def display_menu(line_height=10, spacer=2):
    # shift all item positions down to prevent clipping issues
    pixel_y_shift = 1
    display.fill(0)
    for i in range(min(len(menu_items) - menu_start_index, total_lines)):
        item_index = menu_start_index + i
        print('item_index =', item_index)
        if item_index == selected_index:
            display.fill_rect(0, ((i * (line_height+spacer))-1) +
                              pixel_y_shift, 128, line_height, 1)
            display.text(menu_items[item_index], 0,
                         (i * (line_height+spacer))+pixel_y_shift, 0)
        else:
            display.text(menu_items[item_index], 0,
                         (i * (line_height+spacer))+pixel_y_shift, 1)
    display.show()


def update_encoder_range():
    r.set(min_val=0, max_val=len(menu_items) - 1)


# Initial display
display_menu()
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

        print("--------------------")
        print('selected_index =', val_new)
        print('menu_start_index =', menu_start_index)
        print("--------------------")

        selected_index = val_new
        display_menu()
