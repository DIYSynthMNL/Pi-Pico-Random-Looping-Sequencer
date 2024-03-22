"""
Menu Encoder Filled Rectangles: A menu system example

Move a selection box using an encoder. 
Try to rotate the encoder. You will be able to move the rectangle on the y axis of the screen.
When the button is pressed, the rectangle will move back to the first line.
A height of 10 is used to put text inside the rectangle.

Wiring:
OLED 128x64
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
              min_val=0,
              max_val=4,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)


def button_action(pin, event):
    # set rotary value back to 0 when button is pressed
    if event == Button.PRESSED:
        r.set(value=0)


b = Button(20, internal_pullup=True, callback=button_action)

r.set(value=0)
val_old = -1


def display_menu_line_rect(y_pos=0):
    """The display can handle a max of 5 menu options from y_pos 0 to 4"""
    if y_pos < 0:
        y_pos = 1
    elif y_pos == 0:
        y_pos = 1
    elif y_pos > 0:
        y_pos = (y_pos * 13) + 1
    elif y_pos >= 5:
        print("Rect y_pos exceeded screen bounds")
        y_pos = 53
    display.fill_rect(0, y_pos, 127, 10, 1)


# loop
while True:
    val_new = r.value()
    b.update()

    # move the rectangle selection box when the encoder value has changed
    if val_old != val_new:
        val_old = val_new
        display.fill(0)  # color 1=white, 0=black
        display_menu_line_rect(val_new)
        display.show()
