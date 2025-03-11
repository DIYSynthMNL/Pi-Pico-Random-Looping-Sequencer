import machine
from ssd1306 import SSD1306_I2C

i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
oled = SSD1306_I2C(128, 64, i2c)

oled.text('Hello', 0, 0)
oled.text('World', 0, 10)
oled.show()
