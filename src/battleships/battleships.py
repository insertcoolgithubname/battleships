import random
from enum import Enum
from dataclasses import dataclass
from colorama import init, Fore, Style, Back
from math import ceil
import time
from concurrent.futures import ProcessPoolExecutor
from os import cpu_count


class Orientation(Enum):
    Up = 1
    Right = 2
    Down = 3
    Left = 4


class Strategy():
    """
    The strategy to be used by a player in the battle. Contains methods for picking the next shot coordinates
    made to be overridden by children. The forced_moves variable is a dict of move index and shoot at index.
    """

    def __init__(self, parent_board: 'Board', forced_moves: dict[int, list[int]]):
        self._parent_board: 'Board' = parent_board
        self.hostile_board: 'Board' = None
        self.forced_moves: dict[int, list[int]] = forced_moves
        self.move_history: list['MoveHistoryElement'] = []

    def choose_move(self, move_index: int) -> list[int]:
        if move_index in self.forced_moves:
            return self.forced_moves[move_index]
        # chooses randomly
        return self.choosing_algorithm(move_index=move_index)

    def choosing_algorithm(self, move_index: int) -> list[int]:
        chosen_index = random.choice(self.hostile_board.living_indexes)
        return chosen_index


class RandomStrategy(Strategy):
    def __init__(self, parent_board):
        super().__init__(parent_board=parent_board, forced_moves={})


@dataclass
class MoveHistoryElement():
    total_move_index: int
    "The index in the total (both players) amount of moves"
    move_index: int
    "The index in the player's amount of moves"
    hit_ship: bool
    chosen_index: list[int]


class Board():
    """
    Player's board that contains their fleet.
    """
    def __init__(self, side_length: int, fleet_class: 'Fleet', empty=False,
                 strategy_class: 'Strategy' = RandomStrategy):
        # creates matrix side_length * side_length
        self._side_length = side_length
        self._board_list = [[(OceanBoardElement()) for i in range(side_length)] for j in range(side_length)]
        # argument is actual fleet child class
        self.fleet_object: 'Fleet' = fleet_class()
        # list of references to actual present battleship objects
        self._battleship_list: list['Battleship'] = []

        # first is row index, second is col
        self.ship_occupied_indexes: list[list[int]] = []
        self._restricted_indexes: list[list[int]] = []
        "ships and all tiles adjacent"
        self.shot_at_indexes: list[list[int]] = []
        "Indexes that have already been shot at"
        self._all_indexes: list[list[int]] = []
        "list of all valid indexes of board"
        for i in range(1, self._side_length + 1):
            for j in range(1, self._side_length + 1):
                self._all_indexes.append([i, j])
        self.living_indexes: list[list[int]] = self.all_indexes
        "list of all non shot at indexes of board"
        self.strategy_object: 'Strategy' = strategy_class(parent_board=self)
        if not empty:
            self.add_fleet_to_board()

    @property
    def all_indexes(self):
        return self._all_indexes

    @property
    def board_list(self) -> list:
        return self._board_list

    @property
    def battleship_list(self) -> list['Battleship']:
        return self._battleship_list

    def add_fleet_to_board(self):
        # create all orientations
        all_orientations = [Orientation.Up, Orientation.Right, Orientation.Down, Orientation.Left]

        for ship in self.fleet_object.battleship_list:
            # with restricted indexes excluded
            empty_indexes = [index for index in self._all_indexes if index not in self.restricted_indexes]

            # try up to 500 times and then fail
            success = False
            for repeat in range(500):
                # if all indexes have been exhausted
                if len(empty_indexes) == 0:
                    raise TimeoutError("Could not add ship to board as it is full")
                # pick random index
                chosen_index = random.choice(empty_indexes)
                # exclude this index for future use
                empty_indexes.remove(chosen_index)
                # shuffle orientations so they will be tried in different orders
                random.shuffle(all_orientations)
                # loop trough orienations and try to add ships
                for orientation in all_orientations:
                    if self.add_ship_to_board(ship=ship, index=chosen_index, orientation=orientation):
                        success = True
                        break
                if success is True:
                    break
            if success is False:
                raise TimeoutError("Could not add ship to board in 500 attempts")
        return True

    @property
    def restricted_indexes(self) -> list[list[int]]:
        return self._restricted_indexes

    def shoot_at_index(self, index: list[int]) -> list[bool]:
        """
        Sets shot at of a given index, returns list of bools, first index True if hit ship,
        second if board was destroyed
        """
        element = self.get_element_of_index(index=index)
        element.shot_at = True
        # add to "dead" indexes
        self.shot_at_indexes.append(index)
        # remove from living indexes
        if index in self.living_indexes:
            self.living_indexes.remove(index)
        # For optimalisation (so we dont call is_alive every time)
        hit_ship = False
        if isinstance((self.get_element_of_index(index=index)), BattleshipBoardElement):
            hit_ship = True
            element: BattleshipBoardElement = element
            if element.parent_battleship.destroyed is True:
                return (hit_ship, not (self.is_alive()))
        return [hit_ship, False]

    def refresh_all_ship_destruction(self):
        for ship in self.battleship_list:
            ship.refresh_destroyed()

    def is_alive(self):
        self.refresh_all_ship_destruction()
        alive = False
        for ship in self.battleship_list:
            if not ship.destroyed:
                alive = True
        return alive

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
            # Give ship parent board
            ship.parent_board = self
            # Successful
            return True
        else:
            return False

    def is_in_restricted(self, index: list[int]):
        # if len(self._restricted_indexes) == 0:
        #     return False
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
        self._set_shot_at(new_state=new_state)

    def _set_shot_at(self, new_state):
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
        self._parent_battleship: 'Battleship' = parent_battleship

    @property
    def parent_battleship(self):
        return self._parent_battleship

    @property
    def shot_at(self) -> bool:
        return super().shot_at

    @shot_at.setter
    def shot_at(self, new_state: bool):
        super()._set_shot_at(new_state=new_state)
        self.parent_battleship.refresh_destroyed()

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
        # So the algortihm starts placing large ships
        self._battleship_list.sort(reverse=True)

    @property
    def battleship_list(self):
        return self._battleship_list


# These different fleets should be moved to a config file outside of the script
class BasicFleet(Fleet):
    def __init__(self):
        super().__init__(batlleship_list=[Flagship(), Destroyer(), Destroyer(),
                                          Cruiser(), Cruiser(), Cruiser(),
                                          Scout(), Scout(), Scout(), Scout()
                                          ])


class Battleship():
    def __init__(self, length):
        self._length: int = length
        # len of occupied_indexes must be equal to ship length
        self.occupied_indexes: list[list[int]] = []
        self._parent_board = None
        self._destroyed = False

    # less than for sorting
    def __lt__(self, other):
        return self.length < other.length

    @property
    def destroyed(self):
        return self._destroyed

    @destroyed.setter
    def destroyed(self, new_value):
        # So it only runs on first destruction check
        if new_value is True and self._destroyed is False:
            # shoot at all adjacent indexes
            for index in self.occupied_indexes:
                for adjacent_index in (self.parent_board.get_adjacent_indexes(index=index)):
                    # Can only hit the ocean tiles
                    if isinstance(self.parent_board.get_element_of_index(adjacent_index), OceanBoardElement):
                        self.parent_board.shoot_at_index(index=adjacent_index)
        self._destroyed = new_value

    @property
    def length(self) -> int:
        return self._length

    @property
    def parent_board(self) -> 'Board':
        return self._parent_board

    @parent_board.setter
    def parent_board(self, new_board: 'Board'):
        self._parent_board = new_board

    def refresh_destroyed(self):
        alive = False
        for occupied_index in self.occupied_indexes:
            if self.parent_board.get_element_of_index(index=occupied_index).shot_at is False:
                alive = True
        self.destroyed = not alive


# These different battleships should be moved to a config file outside of the script
class Destroyer(Battleship):
    def __init__(self):
        super().__init__(length=3)


class Flagship(Battleship):
    def __init__(self):
        super().__init__(length=4)


class Cruiser(Battleship):
    def __init__(self):
        super().__init__(length=2)


class Scout(Battleship):
    def __init__(self):
        super().__init__(length=1)


class Battle():
    def __init__(self, strategy1_class: Strategy, strategy2_class: Strategy,
                 fleet: 'Fleet' = BasicFleet, side_length=10, starting_player: int = 1):
        self.board1 = Board(side_length=side_length, fleet_class=fleet, strategy_class=strategy1_class)
        self.board2 = Board(side_length=side_length, fleet_class=fleet, strategy_class=strategy2_class)
        self.board1.strategy_object.hostile_board = self.board2
        self.board2.strategy_object.hostile_board = self.board1

        if starting_player == 1:
            self.starting_player = self.board1
            self.second_player = self.board2
        elif starting_player == 2:
            self.starting_player = self.board2
            self.second_player = self.board1
        elif starting_player == 0:
            self.starting_player = random.choice([self.board1, self.board2])
            if self.starting_player is self.board1:
                self.second_player = self.board2
            if self.starting_player is self.board2:
                self.second_player = self.board1
        else:
            raise ValueError("Wrong starting player, use 1 or 2 to specify player, 0 for random")

    def play(self):
        success = False
        for move in range(1, 501):
            # needs mechanic that allows second move after hit
            # player_to_play is currently last playing player of the last round
            # if the last player hit ship

            # only on the second move and further

            # determines starting player and defines last_player at the end of the first iteration
            if move == 1:
                starting_player_should_play = True
            # last player is defined at the end of the last iteration
            elif last_player.strategy_object.move_history[-1].hit_ship:
                if last_player is self.starting_player:
                    starting_player_should_play = True
                elif last_player is self.second_player:
                    starting_player_should_play = False

            if starting_player_should_play:
                player_to_play = self.starting_player
                waiting_player = self.second_player
            else:
                player_to_play = self.second_player
                waiting_player = self.starting_player

            # proper indexing
            if move != 1:
                if player_to_play is self.board1:
                    if len(self.board1.strategy_object.move_history) == 0:
                        move_index = 1
                    else:
                        move_index = self.board1.strategy_object.move_history[-1].move_index + 1
                elif player_to_play is self.board2:
                    if len(self.board2.strategy_object.move_history) == 0:
                        move_index = 1
                    else:
                        move_index = self.board2.strategy_object.move_history[-1].move_index + 1
            else:
                move_index = 1

            chosen_move = player_to_play.strategy_object.choose_move(move_index=move_index)
            # shoot at the other player
            shoot_bool_list = waiting_player.shoot_at_index(chosen_move)
            move_hit_ship = shoot_bool_list[0]
            move_destroyed_board = shoot_bool_list[1]
            # add to history
            player_to_play.strategy_object.move_history.append(MoveHistoryElement(move_index=move_index,
                                                                                  hit_ship=move_hit_ship,
                                                                                  chosen_index=chosen_move,
                                                                                  total_move_index=move
                                                                                  ))
            # stops when hit destroyed board
            # ~ 3 times faster than asking alive every time

            # needed for next iteration
            last_player = player_to_play
            # switch who should play
            starting_player_should_play = not starting_player_should_play

            # exit the battle if move destroyed board
            if move_destroyed_board:
                success = True
                break
        if success:
            if self.board1.is_alive():
                victorious_player = 1
            if self.board2.is_alive():
                victorious_player = 2
            return BattleSummary(victorious_player=victorious_player,
                                 player1_history=self.board1.strategy_object.move_history,
                                 player2_history=self.board2.strategy_object.move_history)
        else:
            raise TimeoutError("Could not finish battle in 500 tries")


@dataclass
class BattleSummary():
    victorious_player: int
    player1_history: list['MoveHistoryElement']
    player2_history: list['MoveHistoryElement']

    def __str__(self):
        out_str = f"""Player {self.victorious_player} won the game"""
        return out_str


class War():
    def __init__(self, strategy1_class: Strategy, strategy2_class: Strategy, number_of_games: int,
                 fleet: 'Fleet' = BasicFleet, side_length=10, starting_player: int = 1, multiprocess=False):
        """
        Creates an object that runs the number of battles by creating battle objects, running play on them
        and makes a list of battle_summaries which it uses to create war_summary
        which is stored as self.war_summary.\n
        when using multiprocess = True must be called inside if __name__ == "__main__":
        """
        if multiprocess is False:
            self.war_summary = WarSummary()
            for x in range(number_of_games):
                battle_instance = Battle(strategy1_class=strategy1_class, strategy2_class=strategy2_class,
                                         fleet=fleet, side_length=side_length, starting_player=starting_player)
                self.war_summary.battle_summary_list.append(battle_instance.play())
            self.war_summary.calculate_summary()
        elif multiprocess is True:
            self.war_summary = run_war_multiprocessed(strategy1_class=strategy1_class, strategy2_class=strategy2_class,
                                                      number_of_games=number_of_games, fleet=fleet,
                                                      side_length=side_length,
                                                      starting_player=starting_player)


class WarSummary():
    def __init__(self):
        self.battle_summary_list: list['BattleSummary'] = []
        self.number_of_battles: int = 0
        self.player1_victories: int = 0
        self.player2_victories: int = 0
        self.player1_victory_percentage: float = 0
        self.player2_victory_percentage: float = 0

    def calculate_summary(self):
        self.number_of_battles = len(self.battle_summary_list)
        for battle in self.battle_summary_list:
            if battle.victorious_player == 1:
                self.player1_victories += 1
            if battle.victorious_player == 2:
                self.player2_victories += 1
        self.player1_victory_percentage = (self.player1_victories / self.number_of_battles) * 100
        self.player2_victory_percentage = (self.player2_victories / self.number_of_battles) * 100

    def __str__(self):
        out_str = f"""Number of battles: {self.number_of_battles}\n
        Player 1:\n
        Number of victories: {self.player1_victories}\n
        Victory percentage: {round(self.player1_victory_percentage, 3)}%\n
        Player 2:\n
        Number of victories: {self.player2_victories}\n
        Victory percentage: {round(self.player2_victory_percentage, 3)}%\n"""
        return out_str


def merge_war_summaries(war_summaries: list['WarSummary']) -> 'WarSummary':
    out_war_summary = WarSummary()
    for war_summary in war_summaries:
        out_war_summary.battle_summary_list.extend(war_summary.battle_summary_list)
    # recompute summary
    out_war_summary.calculate_summary()
    return out_war_summary


def run_single_war(strategy1_class: Strategy, strategy2_class: Strategy, number_of_games: int,
                   fleet: 'Fleet' = BasicFleet, side_length=10, starting_player: int = 1) -> 'WarSummary':
    """
    Needed for multiprocessing, runs war by the supplied arguments. Identical to creating War object and
    calling .war_summary
    """
    war_instance = War(strategy1_class=strategy1_class, strategy2_class=strategy2_class,
                       number_of_games=number_of_games, fleet=fleet, side_length=side_length,
                       starting_player=starting_player)
    return war_instance.war_summary


def split_evenly(total: int, max_chunks: int) -> list[int]:
    """
    Split 'total' into at most 'max_chunks' positive integers whose sum is 'total',
    and that differ by at most 1.
    Example: total=10, max_chunks=6 -> [2, 2, 2, 2, 1, 1]
    """
    chunks = min(total, max_chunks)  # don't create more chunks than total
    base = total // chunks
    remainder = total % chunks

    out = []
    for i in range(chunks):
        # first 'remainder' chunks get +1
        size = base + (1 if i < remainder else 0)
        out.append(size)
    return out


def run_war_multiprocessed(strategy1_class: Strategy, strategy2_class: Strategy, number_of_games: int,
                           fleet: 'Fleet' = BasicFleet, side_length=10, starting_player: int = 1) -> 'WarSummary':
    # Must be in __name__ == "__main__" or multiprocessing breaks

    # how many cpu cores to use at once
    # there seems to be a small difference between 6 and 12 cores ~15%. Not worth the processor temp
    workers = max(1, int(cpu_count() / 2))

    # make a list like [1667, 1667, 1667, 1667, 1666, 1666]
    chunks = split_evenly(total=number_of_games, max_chunks=workers)

    # multiprocessing
    with ProcessPoolExecutor(max_workers=workers) as pool:
        # futures is a list of future "promises" that the PoolExecutor will run
        # we then use future.result() to get the result of the func after waiting for it to finish

        # creates n wars that are places in queue and workers are going to take them apart one by one
        # is submitted as argument to the submit function, first argument is function to call
        # much faster to call wars by number of workers and distribute their load with the smallest queue possible
        # this is done by the split_evenly function (chunks variable)

        futures = [pool.submit(
                    run_single_war,
                    strategy1_class,
                    strategy2_class,
                    chunk_size,
                    fleet,
                    side_length,
                    starting_player,
                    ) for chunk_size in chunks]

        war_summaries = [f.result() for f in futures]
        out_war_summary = merge_war_summaries(war_summaries=war_summaries)
        return out_war_summary


def main():
    # Multiprocessing Wars
    # Must be in __name__ == "__main__" or multiprocessing breaks

    t0 = time.time()

    my_war = War(strategy1_class=RandomStrategy,
                 strategy2_class=RandomStrategy, number_of_games=1000,
                 starting_player=1, multiprocess=True)
    my_war_summary = my_war.war_summary

    t1 = time.time()

    total = abs(t0 - t1)
    print(f"took {total} seconds with multiprocessing wars")
    print(my_war_summary)

    # t0 = time.time()
    # my_war = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=20000,
    #              starting_player=1)
    # t1 = time.time()

    # total = abs(t0 - t1)

    # print(f"took {total} seconds without multiprocessing")
    # print(my_war.war_summary)


if __name__ == "__main__":
    main()
