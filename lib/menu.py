"""
Coded by DIYSynthMNL

Made to aid in making a menu system for the Pi Pico with an Oled Screen and a rotary encoder

Currently tested and working for 128px * 64px OLED displays

Wiring:
OLED
OLED SDA to GP16
OLED SCL to GP17
OLED VCC to 3.3V
OLED GND to GND

Encoder (no breakout board)
ROT Pin 1 to GP19
ROT Pin 2 to GND
ROT Pin 3 to GP18
SW Pin 1 to GND
SW Pin 2 to GP20

Main menu (Design currently assumes that you only have 1 main menu)
    - has a list of submenus
    - displays current values of children (submenus)
    - can change/edit selected value of a child (submenu)

Submenus (implemented)
    - Single select vertical scroll
        - a list of strings
    - Numerical value range menu
        - a list from min to max value

Submenus (to implement)
    - Button
        - actions: press, hold
    - Screens
        - like a summary of what is going on

# todo put below in a readme
How the menu system works:
SETTING SUBMENUS:
First, you would have to create instances of submenus in your main program.
Then you can put those instances in a list called submenu_list.
Lastly, call the set_submenus().

MAKING THE DISPLAY AND ENCODER DO ITS JOB:
Call loop_main_menu(update_main_program_values_callback=[callback_function]) in a while True loop.
The callback function is for updating the variables used in your main program. It is discussed more in detail below.

GETTING DATA FROM THE MENU SYSTEM INTO YOUR MAIN PROGRAM:
This library only handles the "front end" of your main python program, handling user interaction with the display and the rotary encoder.
It is designed to hold data but you should have variables in your main program so you can access the data easily.
For example, you need to get data from a submenu: you would need to call get_submenu_list() in order to update the main program's variables.
To help you update your main program's variables from the submenus, you will need to provide a callback function in your main program (example: update_values()).
This callback function will only be called when a submenu's selected value has been changed (user pressed the encoder button).
        
TODO code clean up
TODO documentation
TODO screen size constants
TODO screensaver
"""

import machine
from ssd1306 import SSD1306_I2C
from rotary_irq_rp2 import RotaryIRQ
from mp_button import Button

# Pins
SDA_PIN = 16
SCL_PIN = 17
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
ROTARY_CLK_PIN = 18
ROTARY_DT_PIN = 19
ROTARY_BUTTON_PIN = 20

rotary_val_old: int = -1
rotary_val_new: int = 0

rotary = RotaryIRQ(
    pin_num_clk=ROTARY_CLK_PIN,
    pin_num_dt=ROTARY_DT_PIN,
    reverse=False,
    pull_up=True,
    range_mode=RotaryIRQ.RANGE_BOUNDED,
)
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN))
display = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)


class MainMenu:
    def __init__(
        self,
        submenus: list = [],
        submenu_started=False,
        submenu_editing=False,
        current_submenu=None,
        main_menu_started=False,
        submenus_length: int = 0,
        total_lines: int = 4,
        menu_start_index=0,
        highlighted_index=0,
        current_menu_index=-1,
    ):
        self.submenus = submenus
        self.submenu_started = submenu_started
        self.submenu_editing = submenu_editing
        self.current_submenu = current_submenu
        self.main_menu_started = main_menu_started
        self.submenus_length = submenus_length
        self.total_lines = total_lines
        self.menu_start_index = menu_start_index
        self.highlighted_index = highlighted_index
        self.current_menu_index = current_menu_index
        self.button = Button(
            ROTARY_BUTTON_PIN, internal_pullup=True, callback=self.button_action
        )

    def get_button(self) -> Button:
        return self.button

    def set_submenus(self, submenu_list: list) -> None:
        self.submenus = submenu_list
        self.submenus_length = len(submenu_list)

    def draw_main_menu(self) -> None:
        item_index = 0
        pixel_y_shift = 20
        line_height = 10
        spacer = 2

        # draw title bar
        display.fill(0)
        display.text("Main Menu", 2, 4, 1)
        display.rect(0, 0, display.width, 15, 1)

        # draw submenu lines
        # print("---Submenu lines---")
        for i in range(
            min(self.submenus_length - self.menu_start_index, self.total_lines)
        ):
            item_index = self.menu_start_index + i
            submenu_text_line = self.submenus[item_index].__repr__()
            # print(submenu_text_line)
            if item_index == self.highlighted_index:
                # draw highlighted item
                display.fill_rect(
                    0,
                    ((i * (line_height + spacer)) - 1) + pixel_y_shift,
                    display.width,
                    line_height,
                    1,
                )
                display.text(
                    f"{submenu_text_line}",
                    0,
                    (i * (line_height + spacer)) + pixel_y_shift,
                    0,
                )
            else:
                display.text(
                    f"{submenu_text_line}",
                    0,
                    (i * (line_height + spacer)) + pixel_y_shift,
                    1,
                )
        # print("-------------------")
        display.show()

    def scroll_main_menu(self, index) -> None:
        if index > self.menu_start_index + (self.total_lines - 1):
            self.menu_start_index += 1
        if index < self.menu_start_index:
            self.menu_start_index -= 1

    def initialize_main_menu(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = self.highlighted_index
        rotary_val_old = -1
        rotary.set(
            value=self.highlighted_index,
            min_val=0,
            max_val=self.submenus_length - 1,
            incr=1,
        )
        self.main_menu_started = True
        self.draw_main_menu()
        # print("Initialized main menu")

    def read_and_update_rotary_value(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = rotary.value()
        self.button.update()

        if rotary_val_old != rotary_val_new:
            rotary_val_old = rotary_val_new
            self.scroll_main_menu(rotary_val_new)
            self.highlighted_index = rotary_val_new
            self.draw_main_menu()

    def button_action(self, pin, event) -> None:
        global rotary_val_new
        if event == Button.PRESSED:
            print("current_menu_index:", self.current_menu_index)
            if self.current_menu_index == -1:
                # button pressed in main menu
                # latch on submenu selected
                self.current_submenu = self.submenus[self.highlighted_index]
                if isinstance(self.current_submenu, ToggleMenu):
                    self.current_submenu.toggle()
                self.submenu_started = False
                self.submenu_editing = True
            else:
                # button pressed inside a submenu
                self.submenu_started = False
                self.submenu_editing = False
                # change selected on current_submenu
                if self.current_submenu != None:
                    self.current_submenu.set_selected(rotary_val_new)
                # go back to main menu
                self.current_menu_index = -1

    def is_main_menu_loop_exitable(self) -> bool:
        return True if self.submenu_editing is True else False

    def edit_submenu(self) -> None:
        global rotary_val_new
        self.main_menu_started = False
        # start submenu
        if self.submenu_started is False and self.submenu_editing is True:
            if not isinstance(self.current_submenu, ToggleMenu):
                self.current_menu_index = rotary_val_new
            if self.current_submenu is not None:
                if not isinstance(self.current_submenu, ToggleMenu):
                    self.current_submenu.start()
            self.submenu_started = True
        # do submenu update loop
        if self.submenu_started is True and self.submenu_editing is True:
            # print("submenu started and editing")
            if self.current_submenu is not None:
                if not isinstance(self.current_submenu, ToggleMenu):
                    self.current_submenu.read_and_update_rotary_value()
                else:
                    self.submenu_started = False
                    self.submenu_editing = False

    def get_submenu_list(self) -> list:
        return self.submenus

    def loop_main_menu(self, update_main_program_values_callback=None) -> None:
        if not self.is_main_menu_loop_exitable():
            if self.main_menu_started == False:
                self.initialize_main_menu()
            else:
                self.read_and_update_rotary_value()
        else:
            self.edit_submenu()
            if (
                self.submenu_editing is False
                and update_main_program_values_callback is not None
            ):
                update_main_program_values_callback()


class Submenu:
    """A base class of submenus"""

    def __init__(self, name: str, selected, button: Button) -> None:
        self.name = name
        self.selected = selected
        self.button = button


class SingleSelectVerticalScrollMenu(Submenu):
    """
    A submenu type that lets a user select one of the choices from a list of strings
    """

    def __init__(
        self,
        name: str,
        button: Button,
        *,
        selected: str,
        items: list[str],
        total_lines: int = 4,
    ) -> None:
        super().__init__(name, selected, button)
        self.items = items
        self.menu_start_index = 0
        self.total_lines = total_lines
        self.highlighted_index = 0

    def set_selected(self, selected: int) -> None:
        """Sets selected attribute to the referenced index's string value from the items list"""
        self.selected = self.items[selected]

    def set_menu_start_index(self, menu_start_index) -> None:
        """
        menu_start_index determines the first item that will be shown in the display.
        It is used for scrolling.

        For example: a value of 0 will display the first item in the list as the first item in the display
        """
        self.menu_start_index = menu_start_index

    def set_highlighted_index(self, highlighted_index) -> None:
        self.highlighted_index = highlighted_index

    def start(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = 0
        rotary_val_old = -1
        self.menu_start_index = 0
        self.highlighted_index = 0
        rotary.set(value=0, min_val=0, max_val=len(self.items) - 1, incr=1)
        self.display_menu()

    def display_menu(self) -> None:
        item_index = 0
        pixel_y_shift = 20
        line_height = 10
        spacer = 2

        # shift all item positions down to prevent clipping issues
        display.fill(0)
        display.text(
            f"{self.name}:{self.selected if len(
            self.selected) <= 9 else remove_vowels(self.selected)}",
            2,
            4,
            1,
        )
        display.rect(0, 0, 128, 15, 1)
        for i in range(min(len(self.items) - self.menu_start_index, self.total_lines)):
            item_index = self.menu_start_index + i
            if item_index == self.highlighted_index:
                # highlighted item
                display.fill_rect(
                    0,
                    ((i * (line_height + spacer)) - 1) + pixel_y_shift,
                    128,
                    line_height,
                    1,
                )
                # selected
                display.text(
                    (
                        "*" + self.items[item_index]
                        if self.selected == self.items[item_index]
                        else self.items[item_index]
                    ),
                    0,
                    (i * (line_height + spacer)) + pixel_y_shift,
                    0,
                )
            else:
                display.text(
                    (
                        "*" + self.items[item_index]
                        if self.selected == self.items[item_index]
                        else self.items[item_index]
                    ),
                    0,
                    (i * (line_height + spacer)) + pixel_y_shift,
                    1,
                )
        display.show()

    def scroll(self, index):
        # TODO implement rotary range wrap. When at the top (0), go to bottom if moving line up and vise versa.
        if index > self.menu_start_index + (self.total_lines - 1):
            self.menu_start_index += 1
        if index < self.menu_start_index:
            self.menu_start_index -= 1

    def read_and_update_rotary_value(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = rotary.value()
        self.button.update()

        if rotary_val_old != rotary_val_new:
            rotary_val_old = rotary_val_new
            self.scroll(rotary_val_new)
            self.set_highlighted_index(rotary_val_new)
            self.display_menu()
            print("---")
            print("Menu Start Index:", self.menu_start_index)
            print("Highlighted Index:", self.highlighted_index)
            print("Number of submenus:", self.total_lines)
            print("---")

    def __repr__(self) -> str:
        selected_shortened = (
            self.selected if len(self.selected) < 9 else remove_vowels(self.selected)
        )
        return f"{self.name}:{selected_shortened}"


class NumericalValueRangeMenu(Submenu):
    """A submenu type that lets a user change a numerical value within a specified range, increment can also be changed"""

    def __init__(
        self,
        name: str,
        button: Button,
        *,
        selected: int,
        new_value: int = 0,
        min_val: int = 0,
        max_val: int = 100,
        increment: int = 1,
    ) -> None:
        super().__init__(name, selected, button)
        self.new_value = new_value
        self.min_val = min_val
        self.max_val = max_val
        self.increment = increment

    def set_selected(self, selection) -> None:
        self.selected = selection

    def scroll(self, new_value: int) -> None:
        self.new_value = new_value

    def start(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = 0
        rotary_val_old = -1
        rotary.set(
            value=self.selected,
            min_val=self.min_val,
            max_val=self.max_val,
            incr=self.increment,
        )
        self.display_menu()

    def display_menu(self) -> None:
        display.fill(0)
        display.text(self.name, 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        # old value
        display.text(f"Old: {self.selected}", 0, 20, 1)
        if self.new_value == self.selected:
            text = f"New: *{self.new_value}"
        else:
            text = f"New: {self.new_value}"
        display.fill_rect(0, 30, 128, 10, 1)
        display.text(text, 0, 31, 0)
        display.show()

    def read_and_update_rotary_value(self) -> None:
        global rotary_val_new, rotary_val_old
        rotary_val_new = rotary.value()
        self.button.update()
        if rotary_val_old != rotary_val_new:
            rotary_val_old = rotary_val_new
            self.scroll(rotary_val_new)
            self.display_menu()

    def __repr__(self) -> str:
        return f"{self.name}:{self.selected}"


class ToggleMenu(Submenu):
    """A submenu type that lets a user toggle a boolean value using the rotary encoder's button"""

    def __init__(self, name: str, button: Button, *, value: bool) -> None:
        super().__init__(name, value, button)
        self.value = value

    def toggle(self) -> None:
        self.value = not self.value

    def __repr__(self) -> str:
        bool_str = "Off"
        if self.value:
            bool_str = "On"
        else:
            bool_str = "Off"
        return f"{self.name}:{bool_str}"


class CVMenu(Submenu):
    """A submenu type that lets a user see all 4 cv values in realtime"""

    def __init__(
        self,
        name: str,
        button: Button,
    ) -> None:
        super().__init__(name, None, button)

    # TODO


def remove_vowels(word: str) -> str:
    # TODO do not remove leading vowels
    vowels = ["a", "e", "i", "o", "u", "A", "E", "I", "O", "U"]
    return "".join([char for char in word if char not in vowels])
