# Playground — macOS simulator for the sequencer engine

A native macOS playground that runs the same `rls::SequencerEngine` class that
will (later) be linked into a Pico-SDK firmware host. No hardware required.

Built mirroring the pattern documented in the vault note `Quick Tips/Simulating
module UI on macOS` and the reference implementation in
`DIYSynthMNL/vcdo-daisy`. Differences from that reference:

- **No PortAudio.** The sequencer is logic-only; the note's adaptation table
  says to replace audio with a `std::chrono` tick thread. That's what
  `ClockThreadMain` does — sleeps to the next half-period at the configured
  BPM and pulses the engine's `OnClockEdge`.
- **6×8 bitmap font in `FakeOled.h`.** vcdo-daisy didn't need text on its
  fake OLED (just a scope); a sequencer needs "STEP 05/16 BPM 60" so the
  font is inlined here.

## Build

One-time:

```sh
brew install glfw pkg-config
```

Then:

```sh
cd Firmware
make            # first run clones Dear ImGui v1.91.0 into ./imgui/
./playground
# or
make run
```

## What you see

| Window | Contents |
|---|---|
| Sequencer Controls | Transport, BPM, scale combo, starting note, octaves, probabilities, modes |
| Simulated OLED (128×64) | Header bar, status line, 16-step grid (two rows of 8 cells). Current step is filled; trigger-on cells are outlined; out-of-range cells are a single centre pixel. Status text below shows step / DAC / TRIG state |

## Keymap

| Key | Action |
|---|---|
| `S` | Toggle internal clock |
| `G` | Manual clock pulse (works whether internal clock is running or not) |
| `R` | Reset engine (clears CV/trig sequences to defaults, current step to 0) |
| `Esc` / `Q` | Quit |

All other params are driven via ImGui widgets in the Controls window.

## Files

| File | Purpose |
|---|---|
| `SequencerEngine.h`/`.cpp` | Host-agnostic engine. No `<machine>`, no GPIO, no `pico/stdlib.h`. Port of `Software/main.py` |
| `Scales.h` | C++ port of `Software/lib/mcp4725_musical_scales.py` — 46 scale intervals + `BuildScale()` helper |
| `FakeOled.h` | 128×64 monochrome buffer with line/rect/text primitives. 6×8 inline bitmap font |
| `playground.cpp` | macOS host: GLFW + Dear ImGui window, clock thread, key handling, OLED render |
| `Makefile` | macOS-only build recipe (clones ImGui on first run) |

## What's intentionally *not* here

- **Pico-SDK firmware host (`main.cpp`)**. That's the next chunk of work.
  When written, it lives next to this code and links the same
  `SequencerEngine.{h,cpp}` and `Scales.h`. The engine API takes a `now_ms`
  argument exactly so the same code runs under both hosts.
- **The hardware menu UX.** The playground uses ImGui sliders directly to
  drive params — it's for engine development, not menu UX testing. The
  on-OLED menu remains the Pico host's responsibility.

## Tested on

macOS 25.3 (Darwin), Apple clang 17, glfw 3.4, Dear ImGui v1.91.0.
