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


class Menu:
    def __init__(self, name: str, items: list) -> None:
        self.name = name
        self.items = items


class SingleSelectVerticalScrollMenu():
    """
    A menu type that lets the user select a single item from a list of strings

    """
    
    # ! implement oled 

    def __init__(self, name: str, selection: str, items=None) -> None:
        self.name = name
        self.selected = selection
        if items == None:
            items = []
        else:
            self.items = items

    def set_selected(self, selection: str) -> None:
        self.selected = selection

    def get_selected(self) -> str:
        return self.selected


