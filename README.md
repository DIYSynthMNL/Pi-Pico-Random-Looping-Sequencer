# A random generator Eurorack module

Build notes and write-ups on the blog: [diysynthmnl.github.io](https://diysynthmnl.github.io/)

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

## Build status

What's ready for builders today, and what's still on the TODO list:

**Production assets** (what you need to actually fabricate and assemble a final unit)

- [x] Schematic — Rev 0.1.0 ([pi-pico-random-looping-sequencer-schematic-rev-0.1.0.pdf](Hardware/Schematics/pi-pico-random-looping-sequencer-schematic-rev-0.1.0.pdf))
- [ ] PCB layout — in progress — single working layout in `Hardware/pi-pico-random-looping-sequencer/`, not yet separated for fab
- [ ] Gerber files for fabrication — none yet
- [ ] BOM — none yet
- [ ] Final front panel (SVG/PDF for fab) — none yet
- [x] License — [LICENSE](LICENSE)

**Prototype assets** (for breadboard / perfboard / 3D-printed-panel builds before final PCB)

- [x] 3D-printed prototype panel STL — [pico-rand-loop-V2.stl](Hardware/3D%20printed%20panel/pico-rand-loop-V2.stl)

**Documentation**

- [ ] Photos of the assembled module — none yet
- [x] Demo video — [watch](https://youtu.be/u1J9JrJe1Y0)
- [ ] Build / assembly instructions — none yet
- [ ] Calibration / tuning notes — none yet

Want to help fill a gap (build photos, gerbers, an assembly guide)? Open an issue or PR.
