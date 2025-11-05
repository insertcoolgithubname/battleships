import random
from enum import Enum
from dataclasses import dataclass
from colorama import init, Fore, Style, Back


class Orientation(Enum):
    Up = 1
    Right = 2
    Down = 3
    Left = 4


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
        # list of references to actual present battleship objects
        self._battleship_list: list['Battleship'] = []

        # first is row index, second is col
        self.ship_occupied_indexes: list[list[int]] = []
        # ships and all tiles adjacent
        self._restricted_indexes: list[list[int]] = []

    @property
    def board_list(self) -> list:
        return self._board_list

    @property
    def battleship_list(self) -> list:
        return self._battleship_list

    # def shuffle_fleet_position(self):
    #     # picks random non restricted space

    #     # set operations much faster
    #     chosen_row = random.choice(list(set([x for x in range(1, self._side_length)]) - set(self.ship_occupied_indexes[0])))
    #     chosen_col = random.choice(list(set([x for x in range(1, self._side_length)]) - set(self.ship_occupied_indexes[1])))
    #     chosen_space = self._board_list[chosen_row][chosen_col]
    #     print(chosen_space)
    #     # creates the indexes for all ships to be present at
    #     pass

    @property
    def restricted_indexes(self):
        return self._restricted_indexes

    def get_adjacent_indexes(self, index: list[int]) -> list[list[int]]:
        """
        Returns list of adjacent indexes on the board. Does not return invalid indexes outside of the board.
        Does nt include given index
        """
        # goes through 3 indexes (-1, 0, 1) to get full adjacent collumn
        out_index_list = []
        for r in range(-1, 2):
            for s in range(-1, 2):
                if self.is_valid_index(index=[index[0] + r, index[1] + s]):
                    out_index_list.append([index[0] + r, index[1] + s])
        out_index_list.remove(index)
        return out_index_list

    def add_to_restricted_indexes(self, index_list: list[list[int]]):
        """
        Adds the given indexes to the restriced indexes list.
        Also supports a single index as list
        """
        if type(index_list[0]) is int:
            index_list = [index_list]
        for index in index_list:
            if self.is_valid_index(index=index):
                # do not add duplicates
                if (index not in self._restricted_indexes):
                    self._restricted_indexes.append(index)
            else:
                raise IndexError

    def check_if_ship_fits(self, ship: 'Battleship', index: list[int],
                           orientation: 'Orientation' = Orientation.Up) -> bool:
        """
        Takes a Battleship instance and checks if it fits into the board at a given index
         (if it does not overlap any restricted indexes)
        """
        for i in range(ship.length):

            match orientation:
                case Orientation.Up:
                    # move by 1 up the collumn -> must change row index
                    current_index = [index[0] - i, index[1]]
                case Orientation.Right:
                    # move by 1 right the row -> must change col index
                    current_index = [index[0], index[1] + i]
                case Orientation.Down:
                    # move by 1 down the col -> must change row index
                    current_index = [index[0] + i, index[1]]
                case Orientation.Left:
                    # move by 1 left the row -> must change col index
                    current_index = [index[0], index[1] - i]

            if self.is_valid_index(index=current_index):
                # We no longer need to check for adjacency, as we add adjacent indexes to restricted on ship creation
                # # Also cannot be adjacent to a ship
                # for adjacent_index in self.get_adjacent_indexes(index=current_index):
                #     if isinstance((self.get_element_of_index(adjacent_index)), BattleshipBoardElement):
                #         return False
                if self.is_in_restricted(index=current_index):
                    return False
            else:
                return False
        return True

    def add_ship_to_board(self, ship: 'Battleship', index: list[int], orientation: 'Orientation') -> bool:
        """
        Attempts to add ship to board at the given index and orientation,
        returns True if successful, otherwise returns false.
        """
        # This checks if ship fits to board
        if (self.check_if_ship_fits(index=index, orientation=orientation, ship=ship) and
                # Do not add ship if it is already present
                ship not in self._battleship_list):
            for i in range(ship.length):
                match orientation:
                    case Orientation.Up:
                        # move by 1 up the collumn -> must change row index
                        current_index = [index[0] - i, index[1]]
                    case Orientation.Right:
                        # move by 1 right the row -> must change col index
                        current_index = [index[0], index[1] + i]
                    case Orientation.Down:
                        # move by 1 down the col -> must change row index
                        current_index = [index[0] + i, index[1]]
                    case Orientation.Left:
                        # move by 1 left the row -> must change col index
                        current_index = [index[0], index[1] - i]
                # Index is valid (ie ship fits)

                # Actually adding the ship
                # Adds all adjacent indexes of ship into restricted
                self.add_to_restricted_indexes(self.get_adjacent_indexes(current_index))
                # Adds self to restricted indexes
                self.add_to_restricted_indexes(current_index)
                # Sets board element to be ship board element
                self.set_element_of_index(index=current_index,
                                          new_object=BattleshipBoardElement(parent_battleship=ship))
                # Add index to ship inner var ship_occupied_indexes
                ship.occupied_indexes.append(current_index)
            # Add ship to battleship list
            self._battleship_list.append(ship)
            # Successful
            return True
        else:
            return False

    def is_in_restricted(self, index: list[int]):
        for restricted_index in self._restricted_indexes:
            if index[0] == restricted_index[0] and index[1] == restricted_index[1]:
                return True
        return False

    def is_valid_index(self, index: list[int]) -> bool:
        if len(self._board_list[0]) < index[0] or index[0] <= 0:
            return False
        if len(self._board_list[0]) < index[1] or index[1] <= 0:
            return False
        return True

    def get_element_of_index(self, index: list[int]) -> 'BoardElement':
        """
        returns element on the board list specified by index list (first position: row index, second: col index).\n
        Indexes are numbered starting with 1.
        """
        # raise exceptions when indexes are out of range
        if not self.is_valid_index(index=[index[0], 1]):
            raise IndexError("Attempted to get element of invalid row_index")
        if not self.is_valid_index(index=[1, index[1]]):
            raise IndexError("Attempted to get element of invalid col_index")

        return self._board_list[index[0] - 1][index[1] - 1]

    def set_element_of_index(self, index: list[int], new_object) -> bool:
        """
        Sets the board element of given index to be new_object
        """
        # raise exceptions when indexes are out of range
        if not self.is_valid_index(index=[index[0], 1]):
            raise IndexError("Attempted to get element of invalid row_index")
        if not self.is_valid_index(index=[1, index[1]]):
            raise IndexError("Attempted to get element of invalid col_index")

        self._board_list[index[0] - 1][index[1] - 1] = new_object

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
            return f"{Style.DIM}0{Style.RESET_ALL}"
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

    @property
    def parent_battleship(self):
        return self._parent_battleship

    def __str__(self) -> str:
        if self.shot_at is False:
            return f"{Fore.BLUE}S{Fore.RESET}"
        if self.shot_at is True:
            return f"{Fore.RED}X{Fore.RESET}"
        else:
            return ""


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
        self.occupied_indexes: list[list[int]] = []

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


if __name__ == "__main__":
    my_board = Board(side_length=10, fleet_class=BasicFleet)
    # my_board.get_element_of_index(5, 5).shot_at = True
    # print(f"\n{my_board}\n")
    # print(f"shot at: {(my_board.get_element_of_index(index=[1, 1]).shot_at)}")
    ship1 = Destroyer()
    ship2 = Flagship()
    # print(f"the ship fits?: {my_board.check_if_ship_fits(ship=ship, index=[1, 1], orientation=Orientation.Right)}")
    my_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Right)
    my_board.add_ship_to_board(ship=ship2, index=[6, 4], orientation=Orientation.Up)
    print(f"\n{my_board}\n")
    print(my_board._battleship_list[0].occupied_indexes)
    # print(my_board.restricted_indexes)
    # my_board.add_to_restricted_indexes([1, 1])
    # print(my_fleet._battleship_list[0].length)
