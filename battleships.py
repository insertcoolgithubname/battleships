import random
from enum import Enum
from dataclasses import dataclass

class Battle():
    def __init__(self):
        pass


class Board():
    """
    Player's board that contains their fleet.
    """
    def __init__(self, side_length: int):
        # creates matrix side_length * side_length
        self._board_list = [[(BoardElement()) for i in range(side_length)] for j in range(side_length)]
        self.fleet_object = Fleet(self)

    @property
    def board_list(self) -> list:
        return self._board_list

    def get_element_of_index(self, row_index: int, col_index: int) -> 'BoardElement':
        """
        returns element on the board list specified by row_index and col_index.\n
        Indexes are numbered starting with 1.
        """
        # raise exceptions when indexes are out of range
        if len(self._board_list[0]) < row_index:
            raise IndexError("Attempted to get element of invalid row_index")
        if len(self._board_list[0]) < col_index:
            raise IndexError("Attempted to get element of invalid col_index")

        return self._board_list[row_index - 1][col_index - 1]

    def __str__(self):
        """
        returns the entire list printed in user-friendly terms
        """
        # currently does not support different lengths of str(element)
        out_str = ""
        for row_index in range(len(self._board_list)):
            if row_index != 0:
                # new line after row
                out_str = f"{out_str}\n"
            for element in self._board_list[row_index]:
                out_str = f"{out_str} {str(element)}"

        return out_str


class BoardElement():
    """
    the actual value of a square (ie. ocean, unknown, ship, destroyed ship etc.)
    """
    def __init__(self):
        self._shot_at: bool = False

    @property
    def shot_at(self) -> bool:
        return self._shot_at

    @shot_at.setter
    def shot_at(self, new_state: bool):
        """
        set new value of self._shot_at\n
        can techniccally un-shoot a tile
        """
        self._shot_at = new_state

    def __str__(self) -> str:
        if self.shot_at is False:
            return "0"
        if self.shot_at is True:
            return "#"
        else:
            return ""


class OceanBoardElement(BoardElement):
    def __init__(self):
        super().__init__()

    def __str__(self):
        if self.shot_at is True:
            return "#"
        else:
            return super().__str__()


class BattleshipBoardElement(BoardElement):
    def __init__(self, parent_battleship):
        super().__init__()
        self._parent_battleship = parent_battleship

    def __str__(self) -> str:
        if self.shot_at is True:
            return "X"
        else:
            return super().__str__()


class Fleet():
    def __init__(self, parent_board):
        self.parent_board = parent_board
        self._battleship_list = [Destroyer()]


class Battleship():
    def __init__(self, length):
        self._length: int = length

    @property
    def length(self) -> int:
        return self._length


# @dataclass
# how to use dataclasses with super
class Destroyer(Battleship):
    def __init__(self):
        super().__init__(length=3)


my_board = Board(side_length=10)
# my_board.get_element_of_index(5, 5).shot_at = True
# print(my_board)
my_fleet = Fleet(parent_board=my_board)
print(my_fleet._battleship_list[0].length)
