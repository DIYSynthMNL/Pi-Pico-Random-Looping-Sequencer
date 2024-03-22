from machine import Pin
import time

led = Pin(25, Pin.OUT)
led.value(0)

previous_ticks = 0
interval = 200


while True:
    current_ticks = time.ticks_ms()
    if (time.ticks_diff(current_ticks, previous_ticks) > interval):
        previous_ticks = current_ticks
        led.value(0) if led.value() == 1 else led.value(1)
