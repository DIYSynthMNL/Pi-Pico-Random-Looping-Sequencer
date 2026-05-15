// SequencerEngine.h
// Host-agnostic random/looping quantized step sequencer engine.
// Port of the logic in Software/main.py.
//
// Designed so a future polyphonic version (see project_generative_ambient_sequencer
// in Claude memory) can instantiate one of these per voice. No globals, no I/O,
// no time queries — host supplies now_ms.
//
// The two hosts (macOS playground, Pi Pico firmware) own:
//   - clock-edge detection on their respective GPIOs / keyboard
//   - I2C writes to the MCP4725 DAC and digital trigger output
//   - menu rendering on the SSD1306 OLED (or its desktop fake)
//   - the current 12-bit quantizer scale array (this engine reads only)

#pragma once
#include <cstdint>

namespace rls {

constexpr int kMaxSteps        = 16;
constexpr int kMinSteps        = 2;
constexpr int kMaxOctaves      = 5;
constexpr int kMinOctaves      = 1;

// Hardcoded tuning sequence mirroring the Python `tuning_cv_sequence`:
// alternates 12 (~1V) and 24 (~2V) to verify octave spacing on the DAC.
inline constexpr uint16_t kTuningCvSequence[kMaxSteps] = {
  816, 1632, 816, 1632, 816, 1632, 816, 1632,
  816, 1632, 816, 1632, 816, 1632, 816, 1632,
};

struct EngineParams {
  // Sequence length (clamped to [kMinSteps, kMaxSteps])
  int number_of_steps               = 16;

  // Probabilities are 0..100 (percent).
  int cv_probability_of_change      = 0;
  int trig_probability_of_change    = 0;

  // Gate width as a percentage of the measured clock period (0..100).
  int trigger_length_percent        = 50;

  // Mode flags — direct port of the bool toggles in main.py.
  bool is_cv_erase                  = false;  // clamp every step's CV to scale root
  bool is_trig_erase                = false;  // force every step's trigger on
  bool is_test_cv_sequence          = false;  // play the ascending-scale test pattern
  bool is_tuning_cv_sequence        = false;  // play the 1V/2V tuning verification pattern

  // Current 12-bit DAC quantizer scale. Host owns this buffer (typically built
  // by rls::BuildScale into a host-side array on scale/octave/starting-note
  // change). The engine only reads it.
  const uint16_t* current_12bit_scale = nullptr;
  int             scale_length        = 0;
};

class SequencerEngine {
 public:
  void Init();
  void SetParams(const EngineParams& p) { params_ = p; }

  // Host calls on every detected edge of the clock input (rising = clock high).
  // The engine itself does not call any time function — `now_ms` is whatever
  // millisecond clock the host wants to use (e.g. time_us_64()/1000 on Pico,
  // glfwGetTime()*1000 on desktop). Returns true if the step advanced and the
  // host should latch the new DAC / trigger outputs from the accessors below.
  bool OnClockEdge(bool rising, uint32_t now_ms);

  // Host calls regularly (every loop iteration is fine). Turns the trigger
  // output off when its measured-length timer elapses. Returns true if the
  // trigger transitioned off this call.
  bool Tick(uint32_t now_ms);

  // ---- Read-only state for hosts ----
  int       current_step()      const { return current_step_; }
  uint16_t  last_dac()          const { return last_dac_; }
  bool      trig_active()       const { return trigger_active_; }
  uint32_t  last_clock_ms()     const { return clock_ms_; }
  const uint16_t* cv_sequence()      const { return cv_sequence_; }
  const uint8_t*  trigger_sequence() const { return trigger_sequence_; }

 private:
  EngineParams params_{};

  // Sequence state
  uint16_t cv_sequence_[kMaxSteps]      = {0};
  uint8_t  trigger_sequence_[kMaxSteps] = {0};
  uint16_t test_cv_sequence_[kMaxSteps] = {0};

  int      current_step_                = 0;
  bool     step_changed_on_clock_pulse_ = false;

  // Clock timing
  uint32_t previous_clock_ticks_        = 0;
  uint32_t clock_ms_                    = 0;

  // Trigger output timing
  bool     trigger_active_              = false;
  uint32_t trigger_start_ticks_         = 0;
  uint32_t trig_length_ms_              = 0;
  uint32_t ticks_to_trigger_off_        = 0;

  // Last DAC value the host should emit
  uint16_t last_dac_                    = 0;

  // Helpers
  bool ProbabilityRoll(int probability_0_100);
  void RebuildTestSequence();
  void RandomlyChangeCurrentStepCv();
  void RandomlyChangeCurrentStepTrigger();
  uint16_t ScaleRoot() const;
};

}  // namespace rls
