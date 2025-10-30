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
    def __init__(self, side_length: int, fleet_class: 'Fleet'):
        # creates matrix side_length * side_length
        self._side_length = side_length
        self._board_list = [[(BoardElement()) for i in range(side_length)] for j in range(side_length)]
        # argument is actual fleet child class
        self.fleet_object: 'Fleet' = fleet_class()

        # first is row index, second is col
        self.ship_occupied_indexes: list[list[int]] = []
        # ships and all tiles adjacent
        self.restricted_indexes: list[list[int]] = []

    @property
    def board_list(self) -> list:
        return self._board_list

    # def shuffle_fleet_position(self):
    #     # picks random non restricted space
        
    #     # set operations much faster
    #     chosen_row = random.choice(list(set([x for x in range(1, self._side_length)]) - set(self.ship_occupied_indexes[0])))
    #     chosen_col = random.choice(list(set([x for x in range(1, self._side_length)]) - set(self.ship_occupied_indexes[1])))
    #     chosen_space = self._board_list[chosen_row][chosen_col]
    #     print(chosen_space)
    #     # creates the indexes for all ships to be present at
    #     pass

    def check_if_ship_fits(self, ship: 'Battleship', row_index: int, col_index: int):
        """
        Takes a Battleship instance and checks if it fits into the board at a given index
         (if it does not overlap any restricted indexes)
        """
        pass

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
    """
    Configuration/template of what ships are present
    """
    def __init__(self, batlleship_list: list['Battleship']):
        self._battleship_list: list['Battleship'] = batlleship_list


# These different fleets should be moved to a config file outside of the script
class BasicFleet(Fleet):
    def __init__(self):
        super().__init__(batlleship_list=[Destroyer(), Flagship()])


class Battleship():
    def __init__(self, length):
        self._length: int = length
        # len of occupied_indexes must be equal to ship length
        self.occupied_indexes = []

    @property
    def length(self) -> int:
        return self._length


# These different battleships should be moved to a config file outside of the script
class Destroyer(Battleship):
    def __init__(self):
        super().__init__(length=3)


class Flagship(Battleship):
    def __init__(self):
        super().__init__(length=4)


my_board = Board(side_length=10, fleet_class=BasicFleet)

# my_board.get_element_of_index(5, 5).shot_at = True
print(my_board.fleet_object._battleship_list)
# print(my_fleet._battleship_list[0].length)
