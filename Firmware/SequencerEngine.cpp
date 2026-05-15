// SequencerEngine.cpp
// See SequencerEngine.h for the design rationale.

#include "SequencerEngine.h"
#include <cstdlib>   // rand / RAND_MAX

namespace rls {

void SequencerEngine::Init() {
  // Mirror populate_sequence_with_default() — every step starts at scale root,
  // every trigger starts on. If no scale has been supplied yet, default to 0.
  const uint16_t root = ScaleRoot();
  for (int i = 0; i < kMaxSteps; ++i) {
    cv_sequence_[i]      = root;
    trigger_sequence_[i] = 1;
  }
  current_step_                = 0;
  step_changed_on_clock_pulse_ = false;
  previous_clock_ticks_        = 0;
  clock_ms_                    = 0;
  trigger_active_              = false;
  trigger_start_ticks_         = 0;
  trig_length_ms_              = 0;
  ticks_to_trigger_off_        = 0;
  last_dac_                    = root;
  RebuildTestSequence();
}

uint16_t SequencerEngine::ScaleRoot() const {
  return (params_.current_12bit_scale && params_.scale_length > 0)
         ? params_.current_12bit_scale[0]
         : 0;
}

bool SequencerEngine::ProbabilityRoll(int probability_0_100) {
  if (probability_0_100 <= 0)   return false;
  if (probability_0_100 >= 100) return true;
  // Python: random.random() * 100 <= probability  (random.random in [0,1))
  const float r = static_cast<float>(std::rand()) /
                  static_cast<float>(RAND_MAX);
  return r * 100.0f <= static_cast<float>(probability_0_100);
}

void SequencerEngine::RebuildTestSequence() {
  // Fill kMaxSteps cells by cycling the current scale, mirroring
  // get_test_sequence() in main.py.
  if (!params_.current_12bit_scale || params_.scale_length <= 0) {
    for (int i = 0; i < kMaxSteps; ++i) test_cv_sequence_[i] = 0;
    return;
  }
  int idx = 0;
  for (int i = 0; i < kMaxSteps; ++i) {
    test_cv_sequence_[i] = params_.current_12bit_scale[idx];
    idx = (idx + 1) % params_.scale_length;
  }
}

void SequencerEngine::RandomlyChangeCurrentStepCv() {
  if (!params_.current_12bit_scale || params_.scale_length <= 0) return;
  if (!ProbabilityRoll(params_.cv_probability_of_change))        return;
  const int random_idx = std::rand() % params_.scale_length;
  cv_sequence_[current_step_] = params_.current_12bit_scale[random_idx];
}

void SequencerEngine::RandomlyChangeCurrentStepTrigger() {
  if (!ProbabilityRoll(params_.trig_probability_of_change)) return;
  trigger_sequence_[current_step_] =
      static_cast<uint8_t>(std::rand() & 1);
}

bool SequencerEngine::OnClockEdge(bool rising, uint32_t now_ms) {
  // Clamp step bounds — host may have lowered the step count.
  int steps = params_.number_of_steps;
  if (steps < kMinSteps) steps = kMinSteps;
  if (steps > kMaxSteps) steps = kMaxSteps;

  // If we've run past the active sequence length, wrap to 0.
  if (current_step_ >= steps) {
    current_step_ = 0;
  }

  if (rising && !step_changed_on_clock_pulse_) {
    // Rising edge: snapshot ticks, advance the step, write outputs.
    previous_clock_ticks_        = now_ms;
    step_changed_on_clock_pulse_ = true;

    RebuildTestSequence();              // mirror Python ordering
    RandomlyChangeCurrentStepCv();
    RandomlyChangeCurrentStepTrigger();

    if (params_.is_cv_erase) {
      cv_sequence_[current_step_] = ScaleRoot();
    }
    if (params_.is_trig_erase) {
      trigger_sequence_[current_step_] = 1;
    }

    // Pick the CV value to emit on this step.
    if (params_.is_test_cv_sequence) {
      last_dac_ = test_cv_sequence_[current_step_];
    } else if (params_.is_tuning_cv_sequence) {
      last_dac_ = kTuningCvSequence[current_step_];
    } else {
      last_dac_ = cv_sequence_[current_step_];
    }

    // Trigger output: open the gate for trigger_length_percent of the
    // most recently measured clock period.
    trig_length_ms_ = (clock_ms_ * params_.trigger_length_percent) / 100;
    if (trigger_sequence_[current_step_] == 1) {
      trigger_active_       = true;
      trigger_start_ticks_  = now_ms;
      ticks_to_trigger_off_ = now_ms + trig_length_ms_;
    }

    current_step_++;
    return true;
  }

  if (!rising && step_changed_on_clock_pulse_) {
    // Falling edge: remember the clock period for trigger-length math.
    step_changed_on_clock_pulse_ = false;
    // Wrap-safe diff — uint32 subtraction.
    clock_ms_ = now_ms - previous_clock_ticks_;
  }
  return false;
}

bool SequencerEngine::Tick(uint32_t now_ms) {
  if (trigger_active_ && now_ms >= ticks_to_trigger_off_) {
    trigger_active_ = false;
    return true;
  }
  return false;
}

}  // namespace rls
