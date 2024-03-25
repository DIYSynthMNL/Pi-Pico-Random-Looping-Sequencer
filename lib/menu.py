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

# TODO implement rotary encoder
import machine
from ssd1306 import SSD1306_I2C

i2c = machine.I2C(0, sda=machine.Pin(16), scl=machine.Pin(17))
display = SSD1306_I2C(128, 64, i2c)


class SingleSelectVerticalScrollMenu():
    """
    A menu type that lets a user select one of the choices from a list of strings
    
        ATTRIBUTES:
        name: str
            The name that will be displayed on the top
        selected: str
            The current chosen value
        items: list[str]
            List of items to choose from
        total_lines: int (default = 4)
            Total number of selectable item lines to display. 4 would suffice for an oled display with a height of 64px
        highlighted_index: int (default = 0)
            Will determine which line is highlighted or filled. Not intended to be set outside an instance.

    Usage example:
        Initializing:
        menu = m.SingleSelectVerticalScrollMenu(
            name='Scale', selection='chromatic', items=scale_intervals)

        On button press:
        if event == Button.PRESSED:
            current_menu.set_menu_start_index(0)
            current_menu.set_highlighted_index(0)
            current_menu.set_selected_index(val_new)
            r.set(value=0)

        When encoder is rotated:
        only update display if the value has changed
        if val_old != val_new:
            val_old = val_new
            current_menu.scroll(val_new)
            current_menu.set_highlighted_index(val_new)
            current_menu.display_menu()
    """

    global display

    def __init__(self, name: str, *, selected: str, items=None, total_lines: int = 4) -> None:
        self.name = name
        self.selected = selected
        if items == None:
            items = []
        else:
            self.items = items
        self.menu_start_index = 0
        self.total_lines = total_lines
        self.highlighted_index = 0

    def set_selected(self, selected: str) -> None:
        self.selected = selected

    def set_selected_index(self, selected: int) -> None:
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


class NumericalValueRangeMenu():
    global display
    """A menu type that lets a user change a numerical value within a specified range, increment can also be changed"""

    def __init__(self, name: str, *, selected_value: int, new_value: int = 0, min_val: int = 0, max_val: int = 100, increment: int = 1) -> None:
        self.name = name
        self.selected_value = selected_value
        self.new_value = new_value
        self.start = min_val
        self.stop = max_val
        self.increment = increment

    def set_selected(self, selection) -> None:
        self.selected_value = selection

    def scroll(self, new_value: int) -> None:
        self.new_value = new_value

    def display_menu(self) -> None:
        display.fill(0)
        display.text(self.name, 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        # old value
        display.text(f'Old: {self.selected_value}', 0, 20, 1)
        if self.new_value == self.selected_value:
            text = f'New: *{self.new_value}'
        else:
            text = f'New: {self.new_value}'
        display.fill_rect(0, 30, 128, 10, 1)
        display.text(text, 0, 31, 0)
        display.show()


def remove_vowels(word: str) -> str:
    # TODO do not remove leading vowels
    vowels = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
    return ''.join([char for char in word if char not in vowels])
