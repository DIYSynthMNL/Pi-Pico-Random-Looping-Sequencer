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


class SingleSelectVerticalScrollMenu():
    """
    A menu type that lets the user select a single item from a list of strings
    
    Note: Selected and highlighted is different from each other
    Highlighted means...
    Selected means...

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
        # TODO display short version of selected item after name
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


class NumericalValueRangeMenu():
    global display
    """A menu type that lets a user change a numerical value within a specified range, increment can also be changed"""

    def __init__(self, name: str, selected_value: int, new_value: int, start: int, stop: int) -> None:
        self.name = name
        self.selected_value = selected_value
        self.new_value = new_value
        self.start = start
        self.stop = stop

    def set_selected(self, selection) -> None:
        self.selected_value = selection

    def get_selected(self) -> int:
        return self.selected_value

    def scroll(self, new_value: int) -> None:
        self.new_value = new_value

    def get_start_stop(self) -> tuple[int, int]:
        return (self.start, self.stop)

    def display_menu(self) -> None:
        display.fill(0)
        display.text(self.name, 2, 4, 1)
        display.rect(0, 0, 128, 15, 1)
        if self.new_value == self.selected_value:
            text = '*'+str(self.new_value)
        else:
            text = str(self.new_value)
        display.text(text, 46, 36, 1)
        display.show()
