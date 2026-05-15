// playground.cpp
// Native macOS simulator for the Pi-Pico Random Looping Sequencer.
//
// Two ImGui windows:
//   - "OLED 128x64"        : exact pixel-for-pixel render of what the
//                            firmware would show on the SSD1306 — driven
//                            by the same MainMenu class that hardware
//                            will use. Encoder is keyboard-only (left/
//                            right + space) since there's no physical
//                            panel mockup in this build.
//   - "Sequencer Controls" : direct ImGui sliders, bidirectionally synced
//                            with the menu state. Change a slider here →
//                            menu line updates; navigate the menu →
//                            slider follows. Also hosts the internal BPM
//                            clock and a non-hardware engine inspector
//                            (mini step grid).
//
// Architecture (mirrors vcdo-daisy):
//   Main thread     - GUI events, draws ImGui every frame
//   Clock thread    - std::chrono sleep-to-next-tick, fires OnClockEdge
//   Atomic bound    - mutex around EngineParams + menu state
//
// Keymap (matches the note's recommended sequencer layout):
//   Left / Right    : encoder rotate
//   Space           : encoder click
//   G               : manual clock pulse
//   S               : start/stop internal clock
//   R               : reset engine
//   Esc / Q         : quit

#include "SequencerEngine.h"
#include "Scales.h"
#include "FakeOled.h"
#include "Menu.h"

#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"
#include <GLFW/glfw3.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <thread>
#include <vector>

// ============================================================
//  Shared state
// ============================================================
namespace {

std::mutex                 g_mutex;            // guards menu + params + engine
rls::EngineParams          g_params;
rls::SequencerEngine       g_engine;

// Quantizer scale buffer the host owns
uint16_t                   g_scale[rls::kMaxScaleNotes] = {0};
int                        g_scale_count   = 0;
int                        g_scale_idx     = -1;        // index into kScales
int                        g_starting_note = 12;        // mirrors main.py
int                        g_octaves       = 1;

// Internal clock
std::atomic<bool>          g_clock_running{false};
std::atomic<int>           g_bpm{60};
std::atomic<bool>          g_manual_pulse_request{false};
std::atomic<bool>          g_reset_request{false};
std::atomic<bool>          g_app_quitting{false};

// Display-only mirrors for ImGui rendering (avoids holding the mutex
// per frame; torn reads are acceptable for visualization).
std::atomic<int>           g_disp_step{0};
std::atomic<uint16_t>      g_disp_dac{0};
std::atomic<bool>          g_disp_trig{false};
uint16_t                   g_disp_cv[rls::kMaxSteps]   = {0};
uint8_t                    g_disp_trig_grid[rls::kMaxSteps] = {0};

// OLED framebuffer (drawn by Menu, displayed by ImGui)
rls::FakeOled              g_oled;

// ============================================================
//  Menu + submenus
// ============================================================
// The submenus need a stable scale-name list — built once from Scales.h.
std::vector<const char*>   g_scale_names;

rls::MainMenu                          g_menu;
rls::SingleSelectVerticalScrollMenu*   g_scale_menu        = nullptr;
rls::NumericalValueRangeMenu*          g_cv_prob_menu      = nullptr;
rls::NumericalValueRangeMenu*          g_trig_prob_menu    = nullptr;
rls::NumericalValueRangeMenu*          g_trig_length_menu  = nullptr;
rls::NumericalValueRangeMenu*          g_steps_menu        = nullptr;
rls::NumericalValueRangeMenu*          g_octaves_menu      = nullptr;
rls::NumericalValueRangeMenu*          g_start_note_menu   = nullptr;
rls::ToggleMenu*                       g_cv_erase_menu     = nullptr;
rls::ToggleMenu*                       g_trig_erase_menu   = nullptr;
rls::ToggleMenu*                       g_test_seq_menu     = nullptr;
rls::ToggleMenu*                       g_tuning_menu       = nullptr;
std::vector<rls::Submenu*>             g_submenus;

}  // namespace

// ============================================================
//  Scale rebuild — host responsibility
// ============================================================
static void RebuildScale_locked() {
  if (g_scale_idx < 0 || g_scale_idx >= rls::kNumScales) g_scale_idx = 0;
  g_scale_count = rls::BuildScale(rls::kScales[g_scale_idx],
                                  g_starting_note + 12,
                                  g_octaves, g_scale);
  g_params.current_12bit_scale = g_scale;
  g_params.scale_length        = g_scale_count;
}

// ============================================================
//  Menu commit callback — mirrors update_sequencer_values() in main.py
// ============================================================
static void OnMenuCommit(void* /*user*/) {
  // Mutex is NOT held here — host called via OnPress already. The host
  // thread doing the OnPress did so under g_mutex already. So we just
  // pull values straight from submenus.
  const int new_scale_idx = g_scale_menu->selected_index();
  if (new_scale_idx != g_scale_idx) g_scale_idx = new_scale_idx;

  g_params.cv_probability_of_change   = g_cv_prob_menu->selected();
  g_params.trig_probability_of_change = g_trig_prob_menu->selected();
  g_params.trigger_length_percent     = g_trig_length_menu->selected();
  g_params.number_of_steps            = g_steps_menu->selected();
  g_octaves                           = g_octaves_menu->selected();
  g_starting_note                     = g_start_note_menu->selected();
  g_params.is_cv_erase                = g_cv_erase_menu->value();
  g_params.is_trig_erase              = g_trig_erase_menu->value();
  g_params.is_test_cv_sequence        = g_test_seq_menu->value();
  g_params.is_tuning_cv_sequence      = g_tuning_menu->value();

  RebuildScale_locked();
}

// ============================================================
//  Menu setup
// ============================================================
static void BuildMenu() {
  g_scale_idx = rls::FindScaleIndex("major");
  if (g_scale_idx < 0) g_scale_idx = 0;

  g_scale_names.clear();
  g_scale_names.reserve(rls::kNumScales);
  for (int i = 0; i < rls::kNumScales; ++i)
    g_scale_names.push_back(rls::kScales[i].name);

  g_scale_menu       = new rls::SingleSelectVerticalScrollMenu(
      "Scale", g_scale_names.data(), rls::kNumScales, g_scale_idx);
  g_cv_prob_menu     = new rls::NumericalValueRangeMenu("CVProb",    0,  0, 100, 5);
  g_trig_prob_menu   = new rls::NumericalValueRangeMenu("TrigProb",  0,  0, 100, 5);
  g_trig_length_menu = new rls::NumericalValueRangeMenu("TrgLngth%",50,  0, 100, 10);
  g_steps_menu       = new rls::NumericalValueRangeMenu("Steps",    16,
                                                        rls::kMinSteps,
                                                        rls::kMaxSteps, 1);
  g_octaves_menu     = new rls::NumericalValueRangeMenu("Octaves",   1,
                                                        rls::kMinOctaves,
                                                        rls::kMaxOctaves, 1);
  g_start_note_menu  = new rls::NumericalValueRangeMenu("Start note",0,  0, 36, 1);
  g_cv_erase_menu    = new rls::ToggleMenu("CvErase",     false);
  g_trig_erase_menu  = new rls::ToggleMenu("TrigErase",   false);
  g_test_seq_menu    = new rls::ToggleMenu("TestScale",   false);
  g_tuning_menu      = new rls::ToggleMenu("TuningScale", false);

  g_submenus = {
    g_scale_menu, g_cv_prob_menu, g_trig_prob_menu, g_trig_length_menu,
    g_steps_menu, g_octaves_menu, g_start_note_menu,
    g_cv_erase_menu, g_trig_erase_menu, g_test_seq_menu, g_tuning_menu,
  };

  g_menu.SetSubmenus(g_submenus.data(),
                     static_cast<int>(g_submenus.size()));
  g_menu.SetCommitCallback(&OnMenuCommit, nullptr);

  // Initial sync: scale/params from menu defaults.
  OnMenuCommit(nullptr);
  // Engine init after we have a scale.
  g_engine.SetParams(g_params);
  g_engine.Init();
}

// ============================================================
//  Clock thread
// ============================================================
static void ClockThreadMain() {
  using clock_t = std::chrono::steady_clock;
  auto next = clock_t::now();
  bool clock_high = false;

  while (!g_app_quitting.load()) {
    if (g_reset_request.exchange(false)) {
      std::lock_guard<std::mutex> lk(g_mutex);
      g_engine.Init();
    }
    if (g_manual_pulse_request.exchange(false)) {
      const auto now_ms = static_cast<uint32_t>(
          std::chrono::duration_cast<std::chrono::milliseconds>(
              clock_t::now().time_since_epoch()).count());
      std::lock_guard<std::mutex> lk(g_mutex);
      g_engine.SetParams(g_params);
      g_engine.OnClockEdge(true,  now_ms);
      g_engine.OnClockEdge(false, now_ms + 1);
      g_disp_step.store(g_engine.current_step());
      g_disp_dac.store(g_engine.last_dac());
      g_disp_trig.store(g_engine.trig_active());
      std::memcpy(g_disp_cv,        g_engine.cv_sequence(),      sizeof(g_disp_cv));
      std::memcpy(g_disp_trig_grid, g_engine.trigger_sequence(), sizeof(g_disp_trig_grid));
    }

    if (!g_clock_running.load()) {
      const auto now_ms = static_cast<uint32_t>(
          std::chrono::duration_cast<std::chrono::milliseconds>(
              clock_t::now().time_since_epoch()).count());
      {
        std::lock_guard<std::mutex> lk(g_mutex);
        g_engine.Tick(now_ms);
        g_disp_trig.store(g_engine.trig_active());
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
      next = clock_t::now();
      continue;
    }

    const int   bpm         = g_bpm.load();
    const int   period_ms   = (bpm > 0) ? (60000 / bpm) : 1000;
    const auto  half_period = std::chrono::milliseconds(period_ms / 2);

    next += half_period;
    std::this_thread::sleep_until(next);

    clock_high = !clock_high;
    const auto now_ms = static_cast<uint32_t>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            clock_t::now().time_since_epoch()).count());
    {
      std::lock_guard<std::mutex> lk(g_mutex);
      g_engine.SetParams(g_params);
      g_engine.OnClockEdge(clock_high, now_ms);
      g_engine.Tick(now_ms);

      g_disp_step.store(g_engine.current_step());
      g_disp_dac.store(g_engine.last_dac());
      g_disp_trig.store(g_engine.trig_active());
      std::memcpy(g_disp_cv,        g_engine.cv_sequence(),      sizeof(g_disp_cv));
      std::memcpy(g_disp_trig_grid, g_engine.trigger_sequence(), sizeof(g_disp_trig_grid));
    }
  }
}

// ============================================================
//  OLED widget — renders the menu output
// ============================================================
static void RenderOledWidget() {
  {
    std::lock_guard<std::mutex> lk(g_mutex);
    g_menu.Draw(g_oled);
  }

  ImGui::Begin("OLED 128x64");
  ImDrawList* dl = ImGui::GetWindowDrawList();
  ImVec2 p0 = ImGui::GetCursorScreenPos();
  const float scale = 3.0f;
  ImVec2 p1 = ImVec2(p0.x + 128 * scale, p0.y + 64 * scale);
  dl->AddRectFilled(p0, p1, IM_COL32(8, 12, 20, 255));
  for (int y = 0; y < 64; ++y) {
    for (int x = 0; x < 128; ++x) {
      if (g_oled.buf[y * 128 + x]) {
        ImVec2 a(p0.x + x * scale, p0.y + y * scale);
        ImVec2 b(a.x + scale, a.y + scale);
        dl->AddRectFilled(a, b, IM_COL32(180, 220, 255, 255));
      }
    }
  }
  ImGui::Dummy(ImVec2(128 * scale, 64 * scale));
  ImGui::End();
}

// ============================================================
//  Sequencer Controls — direct ImGui sliders, bidirectionally
//  synced with the on-OLED menu state.
// ============================================================
static void RenderControlsWindow() {
  ImGui::Begin("Sequencer Controls");

  ImGui::SeparatorText("Internal clock");
  bool running = g_clock_running.load();
  if (ImGui::Checkbox("Clock running", &running)) g_clock_running.store(running);
  int bpm = g_bpm.load();
  if (ImGui::SliderInt("BPM", &bpm, 20, 240)) g_bpm.store(bpm);

  ImGui::SeparatorText("Direct param edit (syncs to menu)");
  // Snapshot menu state under lock, modify, write back.
  bool changed = false;
  int  cv_prob, trig_prob, trig_len, steps, octs, start_note;
  bool cv_erase, trig_erase, test_seq, tuning;
  int  scale_idx;
  {
    std::lock_guard<std::mutex> lk(g_mutex);
    cv_prob    = g_cv_prob_menu->selected();
    trig_prob  = g_trig_prob_menu->selected();
    trig_len   = g_trig_length_menu->selected();
    steps      = g_steps_menu->selected();
    octs       = g_octaves_menu->selected();
    start_note = g_start_note_menu->selected();
    cv_erase   = g_cv_erase_menu->value();
    trig_erase = g_trig_erase_menu->value();
    test_seq   = g_test_seq_menu->value();
    tuning     = g_tuning_menu->value();
    scale_idx  = g_scale_menu->selected_index();
  }

  if (ImGui::BeginCombo("Scale", rls::kScales[scale_idx].name)) {
    for (int i = 0; i < rls::kNumScales; ++i) {
      bool sel = (i == scale_idx);
      if (ImGui::Selectable(rls::kScales[i].name, sel)) {
        scale_idx = i;
        changed = true;
      }
    }
    ImGui::EndCombo();
  }
  changed |= ImGui::SliderInt("Steps",         &steps,      rls::kMinSteps,   rls::kMaxSteps);
  changed |= ImGui::SliderInt("Octaves",       &octs,       rls::kMinOctaves, rls::kMaxOctaves);
  changed |= ImGui::SliderInt("Start note",    &start_note, 0, 36);
  changed |= ImGui::SliderInt("CV change %",   &cv_prob,    0, 100);
  changed |= ImGui::SliderInt("Trig change %", &trig_prob,  0, 100);
  changed |= ImGui::SliderInt("Trig length %", &trig_len,   0, 100);
  changed |= ImGui::Checkbox ("CV erase",      &cv_erase);
  changed |= ImGui::Checkbox ("Trig erase",    &trig_erase);
  changed |= ImGui::Checkbox ("Test sequence", &test_seq);
  changed |= ImGui::Checkbox ("Tuning seq",    &tuning);

  if (changed) {
    std::lock_guard<std::mutex> lk(g_mutex);
    g_scale_menu->set_selected_index(scale_idx);
    g_cv_prob_menu->set_selected(cv_prob);
    g_trig_prob_menu->set_selected(trig_prob);
    g_trig_length_menu->set_selected(trig_len);
    g_steps_menu->set_selected(steps);
    g_octaves_menu->set_selected(octs);
    g_start_note_menu->set_selected(start_note);
    g_cv_erase_menu->set_value(cv_erase);
    g_trig_erase_menu->set_value(trig_erase);
    g_test_seq_menu->set_value(test_seq);
    g_tuning_menu->set_value(tuning);
    OnMenuCommit(nullptr);  // sync into engine + scale buffer
  }

  ImGui::SeparatorText("Engine inspector");
  ImGui::Text("Step %d   DAC %u   TRIG %s",
              g_disp_step.load(),
              static_cast<unsigned>(g_disp_dac.load()),
              g_disp_trig.load() ? "ON" : "off");
  ImGui::Text("Scale notes: %d", g_scale_count);

  // Mini step grid (engine-state visualization, not on-OLED)
  ImDrawList* dl = ImGui::GetWindowDrawList();
  ImVec2 grid_p0 = ImGui::GetCursorScreenPos();
  const float cell  = 18.0f;
  const float gap   = 3.0f;
  const int   step  = g_disp_step.load();
  for (int i = 0; i < rls::kMaxSteps; ++i) {
    const int   col = i % 8;
    const int   row = i / 8;
    const ImVec2 a(grid_p0.x + col * (cell + gap),
                   grid_p0.y + row * (cell + gap));
    const ImVec2 b(a.x + cell, a.y + cell);
    const bool active_seq = (i < steps);
    const bool has_trig   = g_disp_trig_grid[i] != 0;
    const bool is_cur     = (i + 1 == step) || (step == 0 && i == steps - 1);
    if (!active_seq) {
      dl->AddRect(a, b, IM_COL32(60, 60, 60, 255));
    } else if (is_cur) {
      dl->AddRectFilled(a, b, IM_COL32(255, 200, 80, 255));
    } else if (has_trig) {
      dl->AddRectFilled(a, b, IM_COL32(80, 100, 130, 255));
    } else {
      dl->AddRect(a, b, IM_COL32(120, 120, 120, 255));
    }
  }
  ImGui::Dummy(ImVec2(8 * (cell + gap), 2 * (cell + gap) + 6));
  ImGui::End();
}

// ============================================================
//  Keyboard
// ============================================================
static void OnKey(GLFWwindow* win, int key, int /*sc*/, int action, int /*mods*/) {
  if (action != GLFW_PRESS && action != GLFW_REPEAT) return;
  switch (key) {
    case GLFW_KEY_LEFT: {
      std::lock_guard<std::mutex> lk(g_mutex);
      g_menu.OnRotate(-1);
      break;
    }
    case GLFW_KEY_RIGHT: {
      std::lock_guard<std::mutex> lk(g_mutex);
      g_menu.OnRotate(+1);
      break;
    }
    case GLFW_KEY_SPACE:
      if (action == GLFW_PRESS) {
        std::lock_guard<std::mutex> lk(g_mutex);
        g_menu.OnPress();
      }
      break;
    case GLFW_KEY_G:
      if (action == GLFW_PRESS) g_manual_pulse_request.store(true);
      break;
    case GLFW_KEY_S:
      if (action == GLFW_PRESS) g_clock_running.store(!g_clock_running.load());
      break;
    case GLFW_KEY_R:
      if (action == GLFW_PRESS) g_reset_request.store(true);
      break;
    case GLFW_KEY_ESCAPE:
    case GLFW_KEY_Q:
      if (action == GLFW_PRESS) glfwSetWindowShouldClose(win, GLFW_TRUE);
      break;
    default: break;
  }
}

// ============================================================
//  Entry
// ============================================================
int main() {
  BuildMenu();

  if (!glfwInit()) { std::fprintf(stderr, "glfwInit failed\n"); return 1; }
  glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
  glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
  glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
  glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);

  GLFWwindow* win = glfwCreateWindow(
      1100, 720, "Random Looping Sequencer — Playground",
      nullptr, nullptr);
  if (!win) { glfwTerminate(); return 1; }
  glfwMakeContextCurrent(win);
  glfwSwapInterval(1);
  glfwSetKeyCallback(win, [](GLFWwindow* w, int k, int sc, int a, int m) {
    OnKey(w, k, sc, a, m);
  });

  IMGUI_CHECKVERSION();
  ImGui::CreateContext();
  ImGui::StyleColorsDark();
  ImGui_ImplGlfw_InitForOpenGL(win, true);
  ImGui_ImplOpenGL3_Init("#version 150");

  std::thread clock_thread(ClockThreadMain);

  while (!glfwWindowShouldClose(win)) {
    glfwPollEvents();

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();
    RenderOledWidget();
    RenderControlsWindow();
    ImGui::Render();

    int w, h; glfwGetFramebufferSize(win, &w, &h);
    glViewport(0, 0, w, h);
    glClearColor(0.07f, 0.08f, 0.10f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    glfwSwapBuffers(win);
  }

  g_app_quitting.store(true);
  clock_thread.join();

  ImGui_ImplOpenGL3_Shutdown();
  ImGui_ImplGlfw_Shutdown();
  ImGui::DestroyContext();
  glfwDestroyWindow(win);
  glfwTerminate();

  delete g_scale_menu;       delete g_cv_prob_menu;
  delete g_trig_prob_menu;   delete g_trig_length_menu;
  delete g_steps_menu;       delete g_octaves_menu;
  delete g_start_note_menu;  delete g_cv_erase_menu;
  delete g_trig_erase_menu;  delete g_test_seq_menu;
  delete g_tuning_menu;
  return 0;
}
