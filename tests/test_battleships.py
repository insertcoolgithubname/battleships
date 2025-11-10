from battleships import (Board, BasicFleet, Destroyer, Orientation, Flagship, BattleshipBoardElement,
                         Strategy, RandomStrategy, Battle, War, BattleSummary, WarSummary, merge_war_summaries,
                         run_single_war, split_evenly, run_war_multiprocessed)
import pytest

test_complexity: int = 100
"how many tries for non deterministic tests, must be divisible by 10"


def test_is_valid_index():

    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)

    assert test_board.is_valid_index(index=[1, 1])
    assert test_board.is_valid_index(index=(1, 1))
    # indexes start with 1 (like matrixes in maths)
    assert not test_board.is_valid_index(index=[0, 1])
    assert not test_board.is_valid_index(index=[1, 0])
    assert not test_board.is_valid_index(index=[0, 0])
    # negative indexes not allowed
    assert not test_board.is_valid_index(index=[-1, 1])
    assert not test_board.is_valid_index(index=[1, -1])
    assert not test_board.is_valid_index(index=[-1, -1])
    # indexes larger than length not allowed
    assert not test_board.is_valid_index(index=[1, 11])
    assert not test_board.is_valid_index(index=[11, 1])
    assert not test_board.is_valid_index(index=[11, 11])


def test_add_fleet_to_board():
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    # will successfully complete
    assert test_board.add_fleet_to_board()
    # should also call on creation
    for i in range(int(test_complexity / 10)):
        test_board = Board(side_length=10, fleet_class=BasicFleet)
    # adds all ships from template
    assert len(test_board.fleet_object.battleship_list) == len(test_board.battleship_list)
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    test_board.add_fleet_to_board()
    # Will not fit twice
    with pytest.raises(TimeoutError, match="Could not add ship to board as it is full"):
        test_board.add_fleet_to_board()


def test_add_to_restricted_indexes():
    # Add single index
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    test_board.add_to_restricted_indexes([1, 2])
    test_board.add_to_restricted_indexes([1, 2])
    test_board.add_to_restricted_indexes([3, 8])
    assert [1, 2] in test_board.restricted_indexes
    assert [3, 8] in test_board.restricted_indexes
    assert not ([2, 1] in test_board.restricted_indexes)
    # make sure duplicates are not added
    assert len(test_board.restricted_indexes) == 2

    # Add multiple indexes
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    test_board.add_to_restricted_indexes([[1, 2], [3, 1], [1, 1]])
    assert [1, 2] in test_board.restricted_indexes
    assert [3, 1] in test_board.restricted_indexes
    assert [1, 1] in test_board.restricted_indexes
    assert not ([2, 1] in test_board.restricted_indexes)


def test_get_adjacent_indexes():
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    assert test_board.get_adjacent_indexes([2, 2]) == [
        [1, 1], [1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2], [3, 3]]
    assert test_board.get_adjacent_indexes([1, 2]) == [
        [1, 1], [1, 3], [2, 1], [2, 2], [2, 3]]
    assert test_board.get_adjacent_indexes([1, 10]) == [
        [1, 9], [2, 9], [2, 10]]
    assert test_board.get_adjacent_indexes([10, 10]) == [
        [9, 9], [9, 10], [10, 9]]


def test_shoot_at_index():
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    ship1 = Destroyer()
    ship2 = Destroyer()
    test_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Right)
    test_board.add_ship_to_board(ship=ship2, index=[3, 1], orientation=Orientation.Right)

    test_board.shoot_at_index(index=[1, 1])
    # Shooting will set the target shot_at
    assert test_board.get_element_of_index(index=[1, 1]).shot_at is True
    # Will add to shot at indexes
    assert [1, 1] in test_board.shot_at_indexes
    # Will remove from living indexes
    assert [1, 1] not in test_board.living_indexes
    # Shooting once will not destroy the ship
    assert ship1.destroyed is False
    assert test_board.is_alive() is True
    test_board.shoot_at_index(index=[1, 2])
    assert ship1.destroyed is False
    assert test_board.is_alive() is True
    test_board.shoot_at_index(index=[2, 1])
    # Shooting will set the target shot_at
    assert test_board.get_element_of_index(index=[2, 1]).shot_at is True
    # Shooting into water has no effect on victory
    assert test_board.is_alive() is True
    test_board.shoot_at_index(index=[1, 3])
    # This shot will destroy the ship, second ship remains
    assert ship1.destroyed is True
    # will shoot at all surrounding ocean tiles
    for ship_index in ship1.occupied_indexes:
        for adjacent in test_board.get_adjacent_indexes(index=ship_index):
            assert test_board.get_element_of_index(index=adjacent).shot_at is True
            # will be added to shot at indexes
            assert adjacent in test_board.shot_at_indexes
            # will remove from living indexes
            assert adjacent not in test_board.living_indexes

    # Second ship
    test_board.shoot_at_index(index=[3, 1])
    assert ship2.destroyed is False
    assert test_board.is_alive() is True
    test_board.shoot_at_index(index=[3, 2])
    assert ship2.destroyed is False
    assert test_board.is_alive() is True
    test_board.shoot_at_index(index=[3, 3])
    assert ship2.destroyed is True
    # Entire board is dead
    assert test_board.is_alive() is False


def test_add_ship_to_board():
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    ship1 = Destroyer()
    ship2 = Destroyer()
    ship3 = Flagship()

    # This ship will not fit
    assert not test_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Up)
    # This ship will, ie returns True as successful
    assert test_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Right)
    # Will not add same ship twice
    assert not test_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Right)
    # Correctly added to list
    assert ship1 in test_board.battleship_list
    # All indexes present
    assert len(ship1.occupied_indexes) == ship1.length
    for index in ship1.occupied_indexes:
        assert isinstance((test_board.get_element_of_index(index=index)), BattleshipBoardElement)
        current_board_element: BattleshipBoardElement = test_board.get_element_of_index(index=index)
        # Each board element has proper parent battleship
        assert current_board_element.parent_battleship == ship1
    # Correctly added to restricted indexes
    for index in ship1.occupied_indexes:
        for adjacent_index in test_board.get_adjacent_indexes(index):
            assert adjacent_index in test_board.restricted_indexes
        assert index in test_board.restricted_indexes
    # Ship has proper parent board
    assert ship1.parent_board == test_board

    # Will not fit into the same space
    assert not test_board.add_ship_to_board(ship=ship2, index=[1, 1], orientation=Orientation.Right)
    # Will not fit due to adjacency
    assert not test_board.add_ship_to_board(ship=ship2, index=[2, 1], orientation=Orientation.Right)
    # Will fit as the distance is far enough
    assert test_board.add_ship_to_board(ship=ship2, index=[3, 1], orientation=Orientation.Right)
    # Will fit
    assert test_board.add_ship_to_board(ship=ship3, index=[2, 5], orientation=Orientation.Down)


def test_check_if_ship_fits():

    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    # Testing at empty board

    # Testing out of bounds
    # Cannot fit at edges (destroyer length = 3)
    assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 1], orientation=Orientation.Up)
    assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 1], orientation=Orientation.Left)
    assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 10], orientation=Orientation.Right)
    assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 10], orientation=Orientation.Up)
    # Can fit when oriented right or down
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 1], orientation=Orientation.Right)
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 1], orientation=Orientation.Down)
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 10], orientation=Orientation.Left)
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[1, 10], orientation=Orientation.Down)

    # Testing with restricted
    restricted = [[1, 1], [4, 4]]
    test_board.add_to_restricted_indexes(restricted)

    # Cannot fit into restricted index in any orientation
    for orientation in Orientation:
        assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[4, 4], orientation=orientation)
    # Cannot fit oriented down
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[3, 4], orientation=Orientation.Up)
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[3, 4], orientation=Orientation.Right)
    assert test_board.check_if_ship_fits(ship=Destroyer(), index=[3, 4], orientation=Orientation.Left)
    assert not test_board.check_if_ship_fits(ship=Destroyer(), index=[3, 4], orientation=Orientation.Down)


def test_strategy():
    test_board = Board(side_length=10, fleet_class=BasicFleet, empty=True)
    my_strategy = RandomStrategy(parent_board=test_board)
    my_strategy.hostile_board = test_board
    for x in range(test_complexity):
        chosen_index = my_strategy.choose_move(move_index=x)
        assert chosen_index not in test_board.shot_at_indexes
        assert chosen_index in test_board.living_indexes
        assert chosen_index in test_board.all_indexes
        assert test_board.is_valid_index(chosen_index)
    my_strategy = Strategy(parent_board=test_board, forced_moves={1: [1, 1], 2: [5, 4], 8: [10, 8]})
    my_strategy.hostile_board = test_board
    for x in range(test_complexity):
        chosen_index = my_strategy.choose_move(move_index=1)
        assert chosen_index not in test_board.shot_at_indexes
        assert chosen_index in test_board.living_indexes
        assert chosen_index in test_board.all_indexes
        assert chosen_index == [1, 1]
        chosen_index = my_strategy.choose_move(move_index=x)
        if x == 1:
            assert chosen_index == [1, 1]
        if x == 2:
            assert chosen_index == [5, 4]
        if x == 8:
            assert chosen_index == [10, 8]
        else:
            assert chosen_index in test_board.living_indexes
    my_strategy = RandomStrategy(parent_board=test_board)
    my_strategy.hostile_board = test_board
    assert len(test_board.living_indexes) == 100
    for x in range(1, 101):
        test_board.shoot_at_index(my_strategy.choose_move(move_index=x))
    assert len(test_board.living_indexes) == 0
    with pytest.raises(IndexError, match='Cannot choose from an empty sequence'):
        my_strategy.choose_move(move_index=1)


def test_battle():
    for x in range(test_complexity):
        my_battle = Battle(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, starting_player=1)
        my_battle_summary: 'BattleSummary' = my_battle.play()
        win_number_of_hits = 0
        win_number_of_misses = 0
        other_number_of_hits = 0
        other_number_of_misses = 0
        for index, history_element in enumerate(my_battle_summary.player1_history, start=1):
            assert history_element.move_index == index
            if history_element.hit_ship:
                if my_battle_summary.victorious_player == 1:
                    win_number_of_hits += 1
                if my_battle_summary.victorious_player == 2:
                    other_number_of_hits += 1
            else:
                match my_battle_summary.victorious_player:
                    case 1:
                        win_number_of_misses += 1
                    case 2:
                        other_number_of_misses += 1
            if index != 1:
                # gets the previous element and if it hit, next move should be player1
                if my_battle_summary.player1_history[index - 2].hit_ship is True:
                    assert my_battle_summary.player1_history[index - 2].total_move_index == (
                        history_element.total_move_index - 1)
                # if it missed, the second player must have played
                elif my_battle_summary.player1_history[index - 2].hit_ship is False:
                    # index of missed shot + 1 is not present in player who missed
                    # that means player who missed does not play again
                    index_to_find = my_battle_summary.player1_history[index - 2].total_move_index + 1
                    success = False
                    for local_history_element in my_battle_summary.player1_history:
                        if local_history_element.total_move_index == index_to_find:
                            success = True
                    assert not success
                    # it is present in second player
                    success = False
                    for local_history_element in my_battle_summary.player2_history:
                        if local_history_element.total_move_index == index_to_find:
                            success = True
                    assert success
        # loop through player2 history
        for index, history_element in enumerate(my_battle_summary.player2_history, start=1):
            assert history_element.move_index == index
            if history_element.hit_ship:
                if my_battle_summary.victorious_player == 2:
                    win_number_of_hits += 1
                if my_battle_summary.victorious_player == 1:
                    other_number_of_hits += 1
            else:
                match my_battle_summary.victorious_player:
                    case 1:
                        other_number_of_misses += 1
                    case 2:
                        win_number_of_misses += 1
            if index != 1:
                # gets the previous element and if it hit, next move should be player2
                if my_battle_summary.player2_history[index - 2].hit_ship is True:
                    assert my_battle_summary.player2_history[index - 2].total_move_index == (
                        history_element.total_move_index - 1)
                # if it missed, the second player must have played
                elif my_battle_summary.player2_history[index - 2].hit_ship is False:
                    # index of missed shot + 1 is not present in player who missed
                    index_to_find = my_battle_summary.player2_history[index - 2].total_move_index + 1
                    success = False
                    for local_history_element in my_battle_summary.player2_history:
                        if local_history_element.total_move_index == index_to_find:
                            success = True
                    assert not success
                    # it is present in second player
                    success = False
                    for local_history_element in my_battle_summary.player1_history:
                        if local_history_element.total_move_index == index_to_find:
                            success = True
                    assert success

        # winning player must hit all 20 ship squares
        assert win_number_of_hits == 20
        # losing player cannot hit all 20
        assert other_number_of_hits < 20
        # each board can only hit up to a 100 times on the enemy 10 * 10 grid
        assert len(my_battle_summary.player1_history) <= 100
        assert len(my_battle_summary.player2_history) <= 100
        # one player died
        assert not my_battle.board1.is_alive() or not my_battle.board2.is_alive()
        # number of hits plus misses must equal last move index
        match my_battle_summary.victorious_player:
            case 1:
                assert my_battle_summary.player1_history[-1].move_index == (
                    win_number_of_hits + win_number_of_misses
                )
                assert my_battle_summary.player2_history[-1].move_index == (
                    other_number_of_hits + other_number_of_misses
                )
            case 2:
                assert my_battle_summary.player2_history[-1].move_index == (
                    win_number_of_hits + win_number_of_misses
                )
                assert my_battle_summary.player1_history[-1].move_index == (
                    other_number_of_hits + other_number_of_misses
                )

        # winning player must have taken the last turn
        if my_battle_summary.victorious_player == 1:
            # winning player must have the bigger total move index (took last turn)
            assert my_battle_summary.player1_history[-1].total_move_index > (
                my_battle_summary.player2_history[-1].total_move_index
            )
        if my_battle_summary.victorious_player == 2:
            # winning player must have the bigger total move index (took last turn)
            assert my_battle_summary.player2_history[-1].total_move_index > (
                my_battle_summary.player1_history[-1].total_move_index
            )

        # the total move indexes must match the player indexes combined
        bigger_total_index = max(my_battle_summary.player1_history[-1].total_move_index,
                                 my_battle_summary.player2_history[-1].total_move_index)
        assert bigger_total_index == (my_battle_summary.player1_history[-1].move_index +
                                      my_battle_summary.player2_history[-1].move_index)

        # testing player starting order
        # first player must have the first move out of both
        # if we did not hit first time and should not chain move
        if not my_battle_summary.player1_history[0].hit_ship:
            assert my_battle_summary.player1_history[0].move_index == (
                my_battle_summary.player1_history[0].total_move_index)
            assert my_battle_summary.player1_history[0].total_move_index == 1
        # we hit first hit and should play again (chain move)
        else:
            assert my_battle_summary.player1_history[1].move_index == (
                my_battle_summary.player1_history[1].total_move_index)
            assert my_battle_summary.player1_history[1].total_move_index == 2
        # second player has the second move
        # if we did not hit first time and should not play again
        if not my_battle_summary.player1_history[0].hit_ship:
            assert my_battle_summary.player2_history[0].move_index == (
                my_battle_summary.player2_history[0].total_move_index - 1)
            assert my_battle_summary.player2_history[0].total_move_index == 2
        else:
            assert my_battle_summary.player2_history[0].move_index != (
                my_battle_summary.player2_history[0].total_move_index - 1)
            assert my_battle_summary.player2_history[0].total_move_index != 2
        # the same but with starting player flipped
        my_battle = Battle(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, starting_player=2)
        my_battle_summary: 'BattleSummary' = my_battle.play()
        # first player must have the first move out of both
        # if we did not hit first time and should not play again
        if not my_battle_summary.player2_history[0].hit_ship:
            assert my_battle_summary.player2_history[0].move_index == (
                my_battle_summary.player2_history[0].total_move_index)
            assert my_battle_summary.player2_history[0].total_move_index == 1
        # we hit first hit and should play again
        else:
            assert my_battle_summary.player2_history[1].move_index == (
                my_battle_summary.player2_history[1].total_move_index)
            assert my_battle_summary.player2_history[1].total_move_index == 2
        # second player has the second
        # if we did not hit first time and should not play again
        if not my_battle_summary.player2_history[0].hit_ship:
            assert my_battle_summary.player1_history[0].move_index == (
                my_battle_summary.player1_history[0].total_move_index - 1)
            assert my_battle_summary.player1_history[0].total_move_index == 2
        else:
            assert my_battle_summary.player1_history[0].move_index != (
                my_battle_summary.player1_history[0].total_move_index - 1)
            assert my_battle_summary.player1_history[0].total_move_index != 2


def test_war(my_war_summary=None):
    if my_war_summary is None:
        my_war = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=test_complexity,
                     starting_player=1)
        my_summary = my_war.war_summary
    else:
        my_summary = my_war_summary
    for battle_summary in my_summary.battle_summary_list:
        # testing player starting order
        # first player must have the first move out of both
        # if we did not hit first time and should not play again
        if not battle_summary.player1_history[0].hit_ship:
            assert battle_summary.player1_history[0].move_index == (
                battle_summary.player1_history[0].total_move_index)
            assert battle_summary.player1_history[0].total_move_index == 1
        # we hit first hit and should play again
        else:
            assert battle_summary.player1_history[1].move_index == (
                battle_summary.player1_history[1].total_move_index)
            assert battle_summary.player1_history[1].total_move_index == 2
        # second player has the second
        # if we did not hit first time and should not play again
        if not battle_summary.player1_history[0].hit_ship:
            assert battle_summary.player2_history[0].move_index == (
                battle_summary.player2_history[0].total_move_index - 1)
            assert battle_summary.player2_history[0].total_move_index == 2
        else:
            assert battle_summary.player2_history[0].move_index != (
                battle_summary.player2_history[0].total_move_index - 1)
            assert battle_summary.player2_history[0].total_move_index != 2

    # summary logic works
    number_of_battles = len(my_summary.battle_summary_list)
    player1_victories = 0
    player2_victories = 0
    for battle in my_summary.battle_summary_list:
        if battle.victorious_player == 1:
            player1_victories += 1
        if battle.victorious_player == 2:
            player2_victories += 1
    # inner logic works
    assert my_summary.player1_victory_percentage == (my_summary.player1_victories / my_summary.number_of_battles) * 100
    assert my_summary.player2_victory_percentage == (my_summary.player2_victories / my_summary.number_of_battles) * 100
    # inner logic is equal to test on top
    assert my_summary.player1_victories == player1_victories
    assert my_summary.player2_victories == player2_victories
    assert my_summary.player1_victory_percentage == (player1_victories / number_of_battles) * 100
    assert my_summary.player2_victory_percentage == (player2_victories / number_of_battles) * 100


def test_run_single_war():
    # reusing previous test
    test_war(my_war_summary=run_single_war(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy,
                                           number_of_games=test_complexity,
                                           starting_player=1))


def test_split_evenly():
    assert split_evenly(100, 6) == [17, 17, 17, 17, 16, 16]
    assert split_evenly(99, 6) == [17, 17, 17, 16, 16, 16]
    assert split_evenly(97, 6) == [17, 16, 16, 16, 16, 16]
    assert split_evenly(96, 6) == [16, 16, 16, 16, 16, 16]
    assert split_evenly(95, 6) == [16, 16, 16, 16, 16, 15]
    assert split_evenly(1, 6) == [1]
    assert split_evenly(3, 6) == [1, 1, 1]
    assert split_evenly(6, 6) == [1, 1, 1, 1, 1, 1]

    assert split_evenly(50, 2) == [25, 25]
    assert split_evenly(49, 2) == [25, 24]

    with pytest.raises(ZeroDivisionError, match="integer division or modulo by zero"):
        assert split_evenly(0, 6) == [1]
    with pytest.raises(ZeroDivisionError, match="integer division or modulo by zero"):
        assert split_evenly(3, 0) == [1]

    # weird cases
    assert split_evenly(3, -6) == []
    assert split_evenly(-3, 6) == []

    assert split_evenly(6465, 13) == [498, 498, 498, 498, 497, 497, 497, 497, 497, 497, 497, 497, 497]


def test_run_war_multiprocessed():
    summary = run_war_multiprocessed(
        strategy1_class=RandomStrategy,
        strategy2_class=RandomStrategy,
        number_of_games=test_complexity,   # small!
        starting_player=1,
    )

    # basic sanity checks
    assert summary.number_of_battles == test_complexity
    assert summary.player1_victories + summary.player2_victories == test_complexity
    # percentages should add up to ~100 (float math, so allow small error)
    assert abs((summary.player1_victory_percentage +
                summary.player2_victory_percentage) - 100) < 0.0001

    # reusing test_war code
    test_war(my_war_summary=summary)


def test_war_with_multiprocessing():
    my_war = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=test_complexity,
                 starting_player=1, multiprocess=True)
    test_war(my_war_summary=my_war.war_summary)


def test_merge_war_summary():
    # also sort of tests WarSummary
    war1 = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=test_complexity,
               starting_player=1)
    summary1 = war1.war_summary
    war2 = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=test_complexity,
               starting_player=1)
    summary2 = war2.war_summary
    war3 = War(strategy1_class=RandomStrategy, strategy2_class=RandomStrategy, number_of_games=test_complexity,
               starting_player=1)
    summary3 = war3.war_summary
    merged_summary = merge_war_summaries(war_summaries=[summary1, summary2, summary3])
    assert merged_summary.number_of_battles == (summary1.number_of_battles +
                                                summary2.number_of_battles +
                                                summary3.number_of_battles)
    assert merged_summary.player1_victories == (summary1.player1_victories +
                                                summary2.player1_victories +
                                                summary3.player1_victories)
    assert merged_summary.player2_victories == (summary1.player2_victories +
                                                summary2.player2_victories +
                                                summary3.player2_victories)
    assert merged_summary.player1_victory_percentage == ((merged_summary.player1_victories /
                                                          merged_summary.number_of_battles) * 100)
    assert merged_summary.player2_victory_percentage == ((merged_summary.player2_victories /
                                                          merged_summary.number_of_battles) * 100)
    # contains the entirety of merged summaries
    assert all(elem in (merged_summary.battle_summary_list) for elem in summary1.battle_summary_list)
    assert all(elem in (merged_summary.battle_summary_list) for elem in summary2.battle_summary_list)
    assert all(elem in (merged_summary.battle_summary_list) for elem in summary2.battle_summary_list)
