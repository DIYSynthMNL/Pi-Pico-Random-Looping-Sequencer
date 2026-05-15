// Menu.h
// C++ port of Software/lib/menu.py — the on-OLED menu system driven by
// the rotary encoder + push-button.
//
// Rendering target is an rls::FakeOled instance (the macOS playground)
// or, on hardware, an SSD1306_I2C driver wrapped to expose the same
// primitives (fill/text/rect/fill_rect). The class hierarchy mirrors
// the Python source so behaviour stays one-to-one with the firmware:
//
//   MainMenu                  — list of submenus, scroll + button dispatch
//   Submenu                   — base class
//     SingleSelectVerticalScrollMenu  — choose one of N strings
//     NumericalValueRangeMenu         — int in [min, max] step incr
//     ToggleMenu                      — bool toggle (no separate edit screen)
//
// Encoder interaction model: host calls OnRotate(delta) per detent and
// OnPress() on rotary-button press. The menu owns a `rotary_value`
// bounded to whatever range the current view needs.

#pragma once
#include <cstdint>
#include "FakeOled.h"

namespace rls {

class MainMenu;

// ============================================================
//  Submenu base + concrete kinds
// ============================================================
class Submenu {
 public:
  enum class Kind { kSingleSelect, kNumeric, kToggle };

  Submenu(const char* name, Kind kind) : name_(name), kind_(kind) {}
  virtual ~Submenu() = default;

  const char* name() const { return name_; }
  Kind        kind() const { return kind_; }

  // The one-line "Name:value" representation drawn in the main menu list.
  // Matches Python __repr__ for each subclass.
  virtual void Repr(char* out, int out_cap) const = 0;

  // Called by MainMenu when this submenu is entered (rotary range set, etc.)
  virtual void Start(MainMenu& parent) = 0;

  // Called by MainMenu while this submenu is active. Re-renders if needed.
  virtual void OnRotate(MainMenu& parent, int delta) = 0;

  // Called by MainMenu when the user confirms (button press inside submenu).
  // Returns true if the value actually changed.
  virtual bool Commit(MainMenu& parent) = 0;

  // For ToggleMenu the button press in MainMenu acts directly without a
  // separate edit screen. Returns true for ToggleMenu.
  virtual bool IsToggleStyle() const { return false; }

  // Draw the editor for this submenu (only called when active).
  virtual void Draw(FakeOled& oled) const = 0;

 protected:
  const char* name_;
  Kind        kind_;
};

class SingleSelectVerticalScrollMenu : public Submenu {
 public:
  SingleSelectVerticalScrollMenu(const char* name,
                                 const char* const* items,
                                 int items_count,
                                 int selected_index);

  int  selected_index() const { return selected_index_; }
  void set_selected_index(int idx) { selected_index_ = idx; }
  const char* selected_item() const { return items_[selected_index_]; }

  void Repr(char* out, int out_cap) const override;
  void Start(MainMenu& parent) override;
  void OnRotate(MainMenu& parent, int delta) override;
  bool Commit(MainMenu& parent) override;
  void Draw(FakeOled& oled) const override;

 private:
  void Scroll(int idx);

  const char* const* items_;
  int  items_count_;
  int  selected_index_;
  int  highlighted_index_  = 0;
  int  menu_start_index_   = 0;
  int  total_lines_        = 4;
};

class NumericalValueRangeMenu : public Submenu {
 public:
  NumericalValueRangeMenu(const char* name,
                          int selected, int min_val, int max_val, int increment);

  int  selected() const { return selected_; }
  void set_selected(int v) { selected_ = v; }
  int  min_val()  const { return min_val_; }
  int  max_val()  const { return max_val_; }
  int  increment() const { return increment_; }

  void Repr(char* out, int out_cap) const override;
  void Start(MainMenu& parent) override;
  void OnRotate(MainMenu& parent, int delta) override;
  bool Commit(MainMenu& parent) override;
  void Draw(FakeOled& oled) const override;

 private:
  int selected_;
  int new_value_;
  int min_val_;
  int max_val_;
  int increment_;
};

class ToggleMenu : public Submenu {
 public:
  ToggleMenu(const char* name, bool value);

  bool value() const { return value_; }
  void set_value(bool v) { value_ = v; }

  bool IsToggleStyle() const override { return true; }
  void Repr(char* out, int out_cap) const override;
  void Start(MainMenu& parent) override;     // no-op; ToggleMenu has no edit screen
  void OnRotate(MainMenu& parent, int delta) override;  // no-op
  bool Commit(MainMenu& parent) override;
  void Draw(FakeOled& oled) const override;  // no-op

  // Called by MainMenu directly when its button is pressed and the
  // highlighted submenu is a ToggleMenu — flips the bool, no edit screen.
  bool Toggle() { value_ = !value_; return true; }

 private:
  bool value_;
};

// ============================================================
//  MainMenu — owns the list of submenus and the state machine
// ============================================================
class MainMenu {
 public:
  // The host passes a non-owning array of Submenu*. Lifetime managed by host.
  void SetSubmenus(Submenu* const* submenus, int count);

  // Encoder events.
  void OnRotate(int delta);
  void OnPress();      // rotary button down → debounced press

  // Whether we're currently inside a submenu edit (so renderer knows what to draw).
  bool in_main()        const { return current_menu_index_ < 0 && !submenu_editing_; }
  bool in_submenu()     const { return submenu_editing_; }
  Submenu* current_submenu() const { return current_submenu_; }

  // Render the current view (main list OR active submenu's editor) into oled.
  void Draw(FakeOled& oled) const;

  // ---- Hooks the host registers ----
  // Called once whenever a submenu confirms (the menu returns to main).
  // Lets the host pull all submenu state into engine params at one moment.
  typedef void (*CommitCallback)(void* user);
  void SetCommitCallback(CommitCallback cb, void* user) { commit_cb_ = cb; commit_user_ = user; }

  // ---- Internal state used by Submenu subclasses ----
  // Submenus call these to drive the bounded rotary count when active.
  int  rotary_value() const { return rotary_value_; }
  void set_rotary_bounds(int value, int min_v, int max_v, int incr) {
    rotary_value_ = value;
    rotary_min_   = min_v;
    rotary_max_   = max_v;
    rotary_incr_  = incr;
  }

  int  total_lines()        const { return total_lines_; }
  int  highlighted_index()  const { return highlighted_index_; }
  int  menu_start_index()   const { return menu_start_index_; }

 private:
  void DrawMainList(FakeOled& oled) const;
  void ScrollMainMenu(int index);
  void ApplyRotaryDelta(int delta);

  Submenu* const* submenus_         = nullptr;
  int             submenus_count_   = 0;

  // Main-list scroll state
  int             highlighted_index_ = 0;
  int             menu_start_index_  = 0;
  int             total_lines_       = 4;

  // State machine — mirrors menu.py
  bool            submenu_editing_  = false;
  int             current_menu_index_ = -1;
  Submenu*        current_submenu_   = nullptr;

  // Bounded rotary count (matches the Python `rotary` global state)
  int             rotary_value_ = 0;
  int             rotary_min_   = 0;
  int             rotary_max_   = 0;
  int             rotary_incr_  = 1;

  CommitCallback  commit_cb_   = nullptr;
  void*           commit_user_ = nullptr;
};

// 9-vowel "compact" rendering used by SingleSelectVerticalScrollMenu when
// the selected item name is ≥9 chars. Mirrors Python remove_vowels().
void CompactName(const char* in, char* out, int out_cap);

}  // namespace rls
