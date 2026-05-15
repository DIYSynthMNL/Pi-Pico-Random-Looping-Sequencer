// FakeOled.h
// A 128x64 monochrome framebuffer plus drawing primitives, mirroring what
// you'd write against a real SSD1306 over I2C. The macOS playground draws
// this into the ImGui window scaled up; on hardware the same primitives
// live in the Pico-SDK host file (when written).
//
// The bitmap font is 6x8: glyph bytes are 6 columns × 8 rows, LSB = top.
// Supported glyphs: 0-9, A-Z, space, dash, slash, colon, period, percent,
// asterisk, comma. Anything unsupported renders as a blank.

#pragma once
#include <cstdint>
#include <cstring>
#include <cmath>

namespace rls {

struct FakeOled {
  static constexpr int kW = 128;
  static constexpr int kH = 64;
  uint8_t buf[kW * kH] = {0};        // 0 = off, 255 = on

  void Clear() { std::memset(buf, 0, sizeof(buf)); }

  void Px(int x, int y, bool on) {
    if (x < 0 || x >= kW || y < 0 || y >= kH) return;
    buf[y * kW + x] = on ? 255 : 0;
  }

  void Line(int x0, int y0, int x1, int y1) {
    int dx =  std::abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -std::abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;
    while (true) {
      Px(x0, y0, true);
      if (x0 == x1 && y0 == y1) break;
      int e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  }

  void Rect(int x, int y, int w, int h, bool on = true) {
    for (int i = 0; i < w; ++i) { Px(x + i, y, on); Px(x + i, y + h - 1, on); }
    for (int j = 0; j < h; ++j) { Px(x, y + j, on); Px(x + w - 1, y + j, on); }
  }

  void FillRect(int x, int y, int w, int h, bool on = true) {
    for (int j = 0; j < h; ++j)
      for (int i = 0; i < w; ++i) Px(x + i, y + j, on);
  }

  // 6x8 glyph storage: each glyph is 6 bytes, one per column.
  // Bit 0 (LSB) is the top row.
  static const uint8_t* Glyph(char c) {
    // Built-in glyph table (compact subset).
    static constexpr uint8_t k_space  [6] = {0x00,0x00,0x00,0x00,0x00,0x00};
    static constexpr uint8_t k_dash   [6] = {0x00,0x08,0x08,0x08,0x08,0x00};
    static constexpr uint8_t k_slash  [6] = {0x00,0x60,0x18,0x06,0x01,0x00};
    static constexpr uint8_t k_colon  [6] = {0x00,0x00,0x14,0x00,0x00,0x00};
    static constexpr uint8_t k_period [6] = {0x00,0x00,0x00,0x40,0x00,0x00};
    static constexpr uint8_t k_percent[6] = {0x42,0x21,0x10,0x08,0x44,0x42};
    static constexpr uint8_t k_aster  [6] = {0x00,0x14,0x08,0x14,0x00,0x00};
    static constexpr uint8_t k_comma  [6] = {0x00,0x00,0x40,0x30,0x00,0x00};
    // Digits 0-9
    static constexpr uint8_t k_0[6] = {0x3E,0x51,0x49,0x45,0x3E,0x00};
    static constexpr uint8_t k_1[6] = {0x00,0x42,0x7F,0x40,0x00,0x00};
    static constexpr uint8_t k_2[6] = {0x62,0x51,0x49,0x49,0x46,0x00};
    static constexpr uint8_t k_3[6] = {0x22,0x41,0x49,0x49,0x36,0x00};
    static constexpr uint8_t k_4[6] = {0x18,0x14,0x12,0x7F,0x10,0x00};
    static constexpr uint8_t k_5[6] = {0x2F,0x45,0x45,0x45,0x39,0x00};
    static constexpr uint8_t k_6[6] = {0x3E,0x49,0x49,0x49,0x32,0x00};
    static constexpr uint8_t k_7[6] = {0x01,0x71,0x09,0x05,0x03,0x00};
    static constexpr uint8_t k_8[6] = {0x36,0x49,0x49,0x49,0x36,0x00};
    static constexpr uint8_t k_9[6] = {0x26,0x49,0x49,0x49,0x3E,0x00};
    // Uppercase A-Z
    static constexpr uint8_t k_A[6] = {0x7E,0x11,0x11,0x11,0x7E,0x00};
    static constexpr uint8_t k_B[6] = {0x7F,0x49,0x49,0x49,0x36,0x00};
    static constexpr uint8_t k_C[6] = {0x3E,0x41,0x41,0x41,0x22,0x00};
    static constexpr uint8_t k_D[6] = {0x7F,0x41,0x41,0x22,0x1C,0x00};
    static constexpr uint8_t k_E[6] = {0x7F,0x49,0x49,0x49,0x41,0x00};
    static constexpr uint8_t k_F[6] = {0x7F,0x09,0x09,0x09,0x01,0x00};
    static constexpr uint8_t k_G[6] = {0x3E,0x41,0x49,0x49,0x7A,0x00};
    static constexpr uint8_t k_H[6] = {0x7F,0x08,0x08,0x08,0x7F,0x00};
    static constexpr uint8_t k_I[6] = {0x00,0x41,0x7F,0x41,0x00,0x00};
    static constexpr uint8_t k_J[6] = {0x20,0x40,0x41,0x3F,0x01,0x00};
    static constexpr uint8_t k_K[6] = {0x7F,0x08,0x14,0x22,0x41,0x00};
    static constexpr uint8_t k_L[6] = {0x7F,0x40,0x40,0x40,0x40,0x00};
    static constexpr uint8_t k_M[6] = {0x7F,0x02,0x0C,0x02,0x7F,0x00};
    static constexpr uint8_t k_N[6] = {0x7F,0x04,0x08,0x10,0x7F,0x00};
    static constexpr uint8_t k_O[6] = {0x3E,0x41,0x41,0x41,0x3E,0x00};
    static constexpr uint8_t k_P[6] = {0x7F,0x09,0x09,0x09,0x06,0x00};
    static constexpr uint8_t k_Q[6] = {0x3E,0x41,0x51,0x21,0x5E,0x00};
    static constexpr uint8_t k_R[6] = {0x7F,0x09,0x19,0x29,0x46,0x00};
    static constexpr uint8_t k_S[6] = {0x46,0x49,0x49,0x49,0x31,0x00};
    static constexpr uint8_t k_T[6] = {0x01,0x01,0x7F,0x01,0x01,0x00};
    static constexpr uint8_t k_U[6] = {0x3F,0x40,0x40,0x40,0x3F,0x00};
    static constexpr uint8_t k_V[6] = {0x1F,0x20,0x40,0x20,0x1F,0x00};
    static constexpr uint8_t k_W[6] = {0x7F,0x20,0x18,0x20,0x7F,0x00};
    static constexpr uint8_t k_X[6] = {0x63,0x14,0x08,0x14,0x63,0x00};
    static constexpr uint8_t k_Y[6] = {0x03,0x04,0x78,0x04,0x03,0x00};
    static constexpr uint8_t k_Z[6] = {0x61,0x51,0x49,0x45,0x43,0x00};

    if (c >= 'a' && c <= 'z') c = static_cast<char>(c - 'a' + 'A');
    switch (c) {
      case ' ': return k_space;
      case '-': return k_dash;
      case '/': return k_slash;
      case ':': return k_colon;
      case '.': return k_period;
      case '%': return k_percent;
      case '*': return k_aster;
      case ',': return k_comma;
      case '0': return k_0; case '1': return k_1; case '2': return k_2;
      case '3': return k_3; case '4': return k_4; case '5': return k_5;
      case '6': return k_6; case '7': return k_7; case '8': return k_8;
      case '9': return k_9;
      case 'A': return k_A; case 'B': return k_B; case 'C': return k_C;
      case 'D': return k_D; case 'E': return k_E; case 'F': return k_F;
      case 'G': return k_G; case 'H': return k_H; case 'I': return k_I;
      case 'J': return k_J; case 'K': return k_K; case 'L': return k_L;
      case 'M': return k_M; case 'N': return k_N; case 'O': return k_O;
      case 'P': return k_P; case 'Q': return k_Q; case 'R': return k_R;
      case 'S': return k_S; case 'T': return k_T; case 'U': return k_U;
      case 'V': return k_V; case 'W': return k_W; case 'X': return k_X;
      case 'Y': return k_Y; case 'Z': return k_Z;
      default:  return k_space;
    }
  }

  // Write `s` at (x, y) in white-on-black. Each glyph is 6 pixels wide.
  void Text(int x, int y, const char* s, bool on = true) {
    while (*s) {
      const uint8_t* g = Glyph(*s);
      for (int col = 0; col < 6; ++col) {
        const uint8_t bits = g[col];
        for (int row = 0; row < 8; ++row) {
          if (bits & (1u << row)) Px(x + col, y + row, on);
        }
      }
      x += 6;
      ++s;
    }
  }
};

}  // namespace rls
