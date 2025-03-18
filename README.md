# A random generator Eurorack module

Read the design notes here: [https://diysynthmnl.github.io/p/electric-druid-vcdo/](https://diysynthmnl.github.io/p/electric-druid-vcdo/)

[Demo on YouTube](https://youtu.be/u1J9JrJe1Y0)

## Features

- 128x64 oled screen
- Encoder
- A random step cv sequencer
- A random trigger cv sequencer
- Output cv quantized based on scale chosen
- 4 Analog parameter knobs with inputs

## IO

- 4 Analog knobs with tied inputs with input level knobs
- Trig in
- Digital input
- Digital output
- Analog CV output

## Development instructions

- Turn on the module (eurorack power)
- Plug in the usb (yes it won't damage the pico)

### Developing with VSCode

Use VSCode with the plugin MicroPico

Use the commands while developing:

- Delete all files from pico
- Upload project files to pico
- Run
