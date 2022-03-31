from typing import Any
from .style import Style
from .selectbox import SelectBox

class CheckBox(SelectBox):

    def __init__(self, items, attributes = {}):
        super().__init__(items, attributes)

    def _print_items(self) -> None:
        length = self._attributes["length"]  # Table size to print
        columns = self._attributes["columns"]
        half_length = int(length / columns)
        size = self._attributes["size"]
        pair = 0
        space: str = ' '

        if columns % 2 == 1:
            pair = 1

        for i in range(1, size + 1): # Print the items
            # The width length of the columns plus three spaces of the indicator
            # plus three spaces at the beginning if you enumerate equals true plus the borders
            length_print_space = half_length - (len(self.item_list[i - 1]) + (5 + pair) )

            if self._attributes["enumerate"]:
                length_print_space -= 3
                space *= length_print_space # Space between item and indicator
                msg = f" {i}. {self.item_list[i - 1]}{space}[ ]"
            else:
                space *= length_print_space # Space between item and indicator
                msg = f" {self.item_list[i - 1]}{space}[ ]"
            position = self.item_list[i - 1].getposition
            Style.printxy(position[0], position[1], msg)
            space = ' ' # Reset space

    def _msg(self, item, indi = None): # Returns message for the function previous and the function selects
        length = self._attributes["length"]  # Table size to print
        columns = self._attributes["columns"]
        indicator = self._attributes["indicator"]
        half_length = int(length / columns)
        space = ' '
        pair = 0

        if columns % 2 == 1:
            pair = 1

        indi = ' '
        if self.item_list[item - 1].getmarked:
            indi = indicator

        # The width length of the columns plus three spaces of the indicator
        # plus three spaces at the beginning if you enumerate equals true plus the borders
        half_length -= (len(self.item_list[item - 1]) + (5 + pair))
        if self._attributes["enumerate"]:
            half_length -= 3
        space *= half_length # Space between item and indicator

        if self._attributes["enumerate"]:
            msg = f" {item}. {self.item_list[item - 1]}{space}[{indi}]"
        else:
            msg = f" {self.item_list[item - 1]}{space}[{indi}]"

        return msg

    def _sub_menu_action(self, option):
        Style.cursoron()
        if self.item_list[option - 1].getmarked:
            self.item_list[option - 1]._setmarked(False) # By default setmarked is true
            self._select(option) # mark unmark in real time
        else:
            self.item_list[option - 1]._setmarked(True) # By default setmarked is true
            self._select(option) # mark unmark in real time

    def exit_return(self):
        result = []
        for i in self.item_list:
            result.append((i.index, i.getmarked))
        return result
