"""
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

# Initialize hardware
i2c = machine.I2C(0, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN))
display = SSD1306_I2C(DISPLAY_WIDTH, DISPLAY_HEIGHT, i2c)
r = RotaryIRQ(pin_num_clk=ROTARY_CLK_PIN,
              pin_num_dt=ROTARY_DT_PIN,
              reverse=False,
              pull_up=True,
              range_mode=RotaryIRQ.RANGE_BOUNDED)

# Main menu variables
submenus: list = []
submenu_started = False
submenu_editing = False
current_submenu = None
main_menu_started = False
total_lines: int = 0
menu_start_index = 0
highlighted_index = 0
val_old = -1
val_new = 0

# -1 is the main menu, succeeding ones are 0++
current_menu_index = -1


def set_submenus(submenu_list: list) -> None:
    global submenus, total_lines
    submenus = submenu_list
    total_lines = len(submenu_list)


def display_menu() -> None:
    item_index = 0
    pixel_y_shift = 20
    line_height = 10
    spacer = 2

    # draw title bar
    display.fill(0)
    display.text('Main Menu', 2, 4, 1)
    display.rect(0, 0, display.width, 15, 1)

    # draw submenu lines
    for i in range(min(total_lines - menu_start_index, total_lines)):
        item_index = menu_start_index + i
        submenu_text_line = submenus[item_index].__repr__()
        if item_index == highlighted_index:
            # draw highlighted item
            display.fill_rect(0, ((i * (line_height+spacer))-1) +
                              pixel_y_shift, display.width, line_height, 1)
            display.text(f'{submenu_text_line}', 0,
                         (i*(line_height+spacer))+pixel_y_shift, 0)
        else:
            display.text(f'{submenu_text_line}', 0,
                         (i*(line_height+spacer))+pixel_y_shift, 1)
    display.show()


def scroll(index) -> None:
    global menu_start_index
    if index > menu_start_index + (total_lines-1):
        menu_start_index += 1
    if index < menu_start_index:
        menu_start_index -= 1


def start() -> None:
    global val_new, val_old, menu_start_index, highlighted_index, main_menu_started
    val_new = 0
    val_old = -1
    menu_start_index = 0
    highlighted_index = 0
    r.set(value=0, min_val=0, max_val=total_lines-1, incr=1)
    main_menu_started = True
    display_menu()


def update() -> None:
    global val_old, highlighted_index
    val_new = r.value()
    b.update()

    if val_old != val_new:
        val_old = val_new
        scroll(val_new)
        highlighted_index = val_new
        display_menu()


def button_action(pin, event) -> None:
    global current_submenu, submenu_started, submenu_editing, current_menu_index
    if event == Button.PRESSED:
        if current_menu_index == -1:
            # button pressed in main menu
            # latch on submenu selected
            print(f'Submenus size:{len(submenus)}')
            current_submenu = submenus[highlighted_index]
            print(f'Highlighted index: {highlighted_index}')
            print(f'Current submenu:{current_submenu.__repr__()}')
            submenu_started = False
            submenu_editing = True
        else:
            # button pressed in submenus
            print('Submenu button pressed')
            submenu_started = False
            submenu_editing = False
            # change selected on current_submenu
            if current_submenu != None:
                current_submenu.set_selected(val_new)
            # go back to main menu
            current_menu_index = -1


b = Button(ROTARY_BUTTON_PIN, internal_pullup=True, callback=button_action)


def exit_main_menu_loop() -> bool:
    return True if submenu_editing is True else False


def edit_submenu() -> None:
    global submenu_started, current_menu_index, main_menu_started
    main_menu_started = False
    # start submenu
    if submenu_started is False and submenu_editing is True:
        current_menu_index = val_new
        if current_submenu is not None:
            current_submenu.start()
        submenu_started = True
    # do submenu update loop
    if submenu_started is True and submenu_editing is True:
        if current_submenu is not None:
            current_submenu.update()


def get_submenu_list() -> list:
    return submenus


def loop_main_menu(update_main_program_values_callback=None) -> None:
    if not exit_main_menu_loop():
        if main_menu_started == False:
            start()
        else:
            update()
    else:
        edit_submenu()
        if submenu_editing is False and update_main_program_values_callback is not None:
            update_main_program_values_callback()
            
class Submenu():
    """A base class of submenus"""
    def __init__(self, name: str, selected) -> None:
        self.name = name
        self.selected = selected


class SingleSelectVerticalScrollMenu(Submenu):
    """
    A submenu type that lets a user select one of the choices from a list of strings
    """

    global display

    def __init__(self, name: str, *, selected: str, items: list[str], total_lines: int = 4) -> None:
        super().__init__(name, selected)
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
        global val_old, val_new
        val_new = 0
        val_old = -1
        self.menu_start_index = 0
        self.highlighted_index = 0
        r.set(value=0, min_val=0, max_val=len(self.items)-1, incr=1)
        self.display_menu()

    def display_menu(self) -> None:
        item_index = 0
        pixel_y_shift = 20
        line_height = 10
        spacer = 2

        # shift all item positions down to prevent clipping issues
        display.fill(0)
        display.text(f'{self.name}:{self.selected if len(
            self.selected) <= 9 else remove_vowels(self.selected)}', 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        for i in range(min(len(self.items) - self.menu_start_index, self.total_lines)):
            item_index = self.menu_start_index + i
            if item_index == self.highlighted_index:
                # highlighted item
                display.fill_rect(0, ((i * (line_height+spacer))-1) +
                                  pixel_y_shift, 128, line_height, 1)
                # selected
                display.text('*' + self.items[item_index] if self.selected == self.items[item_index] else self.items[item_index], 0,
                             (i * (line_height+spacer))+pixel_y_shift, 0)
            else:
                display.text('*' + self.items[item_index] if self.selected == self.items[item_index] else self.items[item_index], 0,
                             (i * (line_height+spacer))+pixel_y_shift, 1)
        display.show()

    def scroll(self, index):
        # TODO implement rotary range wrap. When at the top (0), go to bottom if moving line up and vise versa.
        if index > self.menu_start_index + (self.total_lines-1):
            self.menu_start_index += 1
        if index < self.menu_start_index:
            self.menu_start_index -= 1

    def update(self) -> None:
        global val_old, val_new
        val_new = r.value()
        b.update()

        if val_old != val_new:
            val_old = val_new
            self.scroll(val_new)
            self.set_highlighted_index(val_new)
            self.display_menu()

    def __repr__(self) -> str:
        selected_shortened = self.selected if len(
            self.selected) < 9 else remove_vowels(self.selected)
        return f'{self.name}:{selected_shortened}'


class NumericalValueRangeMenu(Submenu):
    global display
    """A submenu type that lets a user change a numerical value within a specified range, increment can also be changed"""

    def __init__(self, name: str, *, selected: int, new_value: int = 0, min_val: int = 0, max_val: int = 100, increment: int = 1) -> None:
        super().__init__(name, selected)
        self.new_value = new_value
        self.min_val = min_val
        self.max_val = max_val
        self.increment = increment

    def set_selected(self, selection) -> None:
        self.selected = selection

    def scroll(self, new_value: int) -> None:
        self.new_value = new_value

    def start(self) -> None:
        global val_old, val_new
        val_new = 0
        val_old = -1
        r.set(value=self.selected, min_val=self.min_val,
              max_val=self.max_val, incr=self.increment)
        self.display_menu()

    def display_menu(self) -> None:
        display.fill(0)
        display.text(self.name, 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        # old value
        display.text(f'Old: {self.selected}', 0, 20, 1)
        if self.new_value == self.selected:
            text = f'New: *{self.new_value}'
        else:
            text = f'New: {self.new_value}'
        display.fill_rect(0, 30, 128, 10, 1)
        display.text(text, 0, 31, 0)
        display.show()

    def update(self) -> None:
        global val_new, val_old
        val_new = r.value()
        b.update()
        if val_old != val_new:
            val_old = val_new
            self.scroll(val_new)
            self.display_menu()

    def __repr__(self) -> str:
        return f'{self.name}:{self.selected}'


def remove_vowels(word: str) -> str:
    # TODO do not remove leading vowels
    vowels = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
    return ''.join([char for char in word if char not in vowels])
