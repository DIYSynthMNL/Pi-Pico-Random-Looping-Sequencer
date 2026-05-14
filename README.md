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

What's available for builders, and what's still on the TODO list:

- [x] Schematic PDF (latest Rev 0.1.0) — [pi-pico-random-looping-sequencer-schematic-rev-0.1.0.pdf](Hardware/Schematics/pi-pico-random-looping-sequencer-schematic-rev-0.1.0.pdf)
- [ ] KiCad source files — *not yet*
- [ ] Gerber files for PCB fabrication — *not yet exported — generate from kicad/ before sending to a fab*
- [ ] Bill of materials (BOM) — *not yet exported*
- [x] 3D-printed front panel STL — [pico-rand-loop-V2.stl](Hardware/3D%20printed%20panel/pico-rand-loop-V2.stl)
- [ ] Front panel graphics (SVG/PDF for fab-made panels) — *not yet exported*
- [ ] Photos of the assembled module — *not yet — coming soon*
- [x] Demo video — [watch](https://youtu.be/u1J9JrJe1Y0)
- [ ] Build / assembly instructions — *not yet written*
- [ ] Calibration / tuning notes — *not yet written*
- [x] License — [LICENSE](LICENSE)

If you want to help fill a gap (build photos, gerbers, an assembly guide), open an issue or PR.
