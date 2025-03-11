include <EuroPanelMaker/panel.scad>

hp = 12;
title = "PicoRandSeq";
title_font_size = 3;
title_font = "Alte Haas Grotesk:style=bold";
label_font = "Alte Haas Grotesk:style=bold";

panel_flipped=true;
pin_alignment_mode = true;
vertical_mode_254 = true;

jacks = [
[1.5, 16, "A1"],
[4.5, 16, "A2"],
[7.5, 16, "A3"],
[10.5, 16, "A4"],

[1.5, 8, "Trig In"],
[4.5, 8, "Din"],
[7.5, 8, "Dout"],
[10.5, 8, "Aout"],
];

encoders = [
[9, 38, ""] // encoder
];

pots_rd901f = [
// Level
[1.5, 28, "A1"],
[4.5, 28, "A2"],
[7.5, 28, "A3"],
[10.5, 28, "A4"],


// Amplitude
[1.5, 21, ""], //A1
[4.5, 21, ""], //A2
[7.5, 21, ""], //A3
[10.5, 21, ""], //A4
];

rectangular_holes = [
//ssd1306 128x64 px
[4.5, 104, 23, 12, 30, 30]
];
generatePanel();