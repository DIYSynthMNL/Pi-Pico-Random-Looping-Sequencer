import machine
import mcp4725

i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
print(i2c.scan())

dac = mcp4725.MCP4725(i2c, mcp4725.BUS_ADDRESS[0])
dac.write(1200)
