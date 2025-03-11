import machine
from ssd1306 import SSD1306_I2C

i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
print(i2c.scan())

display = SSD1306_I2C(128, 64, i2c)

display.fill(0)
display.fill_rect(0, 0, 32, 32, 1)
display.fill_rect(2, 2, 28, 28, 0)
display.vline(9, 8, 22, 1)
display.vline(16, 2, 22, 1)
display.vline(23, 8, 22, 1)
display.fill_rect(26, 24, 2, 4, 1)
display.text('MicroPython', 40, 0, 1)
display.text('SSD1306', 40, 12, 1)
display.text('OLED 128x64', 40, 24, 1)
display.show()
