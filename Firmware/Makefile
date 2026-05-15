# Makefile for the Random Looping Sequencer playground (macOS, Homebrew toolchain).
#
# Prereqs (one-time):
#   brew install glfw pkg-config
#
# Then to build and run:
#   make             # builds ./playground
#   make run         # builds and runs
#
# Dear ImGui is vendored into ./imgui/ on first build via git clone.

CXX      = clang++
CXXFLAGS = -std=c++17 -O2 -Wall -Wno-unused-parameter -DGL_SILENCE_DEPRECATION
INCLUDES = -I. -Iimgui -Iimgui/backends $(shell pkg-config --cflags glfw3)
LIBS     = $(shell pkg-config --libs glfw3) \
           -framework OpenGL -framework Cocoa -framework IOKit -framework CoreVideo

IMGUI_SRCS = imgui/imgui.cpp imgui/imgui_draw.cpp imgui/imgui_tables.cpp \
             imgui/imgui_widgets.cpp \
             imgui/backends/imgui_impl_glfw.cpp \
             imgui/backends/imgui_impl_opengl3.cpp

ENGINE_SRCS = SequencerEngine.cpp Menu.cpp

ENGINE_HDRS = SequencerEngine.h Scales.h FakeOled.h Menu.h

all: playground

imgui/imgui.cpp:
	@echo "Cloning Dear ImGui v1.91.0..."
	git clone --depth 1 --branch v1.91.0 https://github.com/ocornut/imgui imgui

playground: playground.cpp $(ENGINE_SRCS) $(ENGINE_HDRS) $(IMGUI_SRCS) | imgui/imgui.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) playground.cpp $(ENGINE_SRCS) $(IMGUI_SRCS) -o $@ $(LIBS)

run: playground
	./playground

clean:
	rm -f playground

# `make distclean` also removes the cloned Dear ImGui dir.
distclean: clean
	rm -rf imgui

.PHONY: all run clean distclean
