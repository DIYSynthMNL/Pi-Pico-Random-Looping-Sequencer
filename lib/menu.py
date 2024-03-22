"""
Made to aid in making a menu system for the Pi Pico with an Oled Screen

Menu types:
- Main menu
    - can have a list of children (sub menus)
    - display current value of children
- Single select vertical scroll
    - traverse through a list
- Numerical list
    - has a list of numbers
- Numerical range
    - create a list from first, and last number
- Numerical percent (0-100)

"""
import machine
from ssd1306 import SSD1306_I2C
i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
display = SSD1306_I2C(128, 64, i2c)


class Menu:
    def __init__(self, name: str, items: list) -> None:
        self.name = name
        self.items = items
        # ! initialize display


class SingleSelectVerticalScrollMenu():
    """
    A menu type that lets the user select a single item from a list of strings

    """
    global display

    def __init__(self, name: str, selection: str, items=None, total_lines=4) -> None:
        self.name = name
        self.selected = selection
        if items == None:
            items = []
        else:
            self.items = items
        self.menu_start_index = 0
        self.total_lines = total_lines
        self.highlighted_index = 0

    def set_selected(self, selection: str) -> None:
        # use when button is pressed
        self.selected = selection
        
    def set_selected_index(self, selection: int) -> None:
        self.selected = self.items[selection]

    def get_selected(self) -> str:
        return self.selected

    def set_menu_start_index(self, menu_start_index) -> None:
        self.menu_start_index = menu_start_index

    def set_highlighted_index(self, highlighted_index) -> None:
        self.highlighted_index = highlighted_index

    def display_menu(self) -> None:
        item_index = 0
        pixel_y_shift = 20
        line_height = 10
        spacer = 2

        # shift all item positions down to prevent clipping issues
        display.fill(0)
        display.text(self.name, 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        for i in range(min(len(self.items) - self.menu_start_index, self.total_lines)):
            item_index = self.menu_start_index + i
            if item_index == self.highlighted_index:
                # highlighted item
                display.fill_rect(0, ((i * (line_height+spacer))-1) +
                                  pixel_y_shift, 128, line_height, 1)
                display.text('*' + self.items[item_index] if self.selected == self.items[item_index] else self.items[item_index], 0,
                             (i * (line_height+spacer))+pixel_y_shift, 0)
            else:
                display.text('*' + self.items[item_index] if self.selected == self.items[item_index] else self.items[item_index], 0,
                             (i * (line_height+spacer))+pixel_y_shift, 1)
        display.show()

    def scroll(self, index):
        if index > self.menu_start_index + (self.total_lines-1):
            self.menu_start_index += 1
        if index < self.menu_start_index:
            self.menu_start_index -= 1
