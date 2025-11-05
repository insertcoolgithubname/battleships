from battleships import Board, BasicFleet, Destroyer, Orientation, Flagship, BattleshipBoardElement


def test_is_in_restricted():

    test_board = Board(side_length=10, fleet_class=BasicFleet)

    assert test_board.is_valid_index(index=[1, 1])
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


def test_add_to_restricted_indexes():
    # Add single index
    test_board = Board(side_length=10, fleet_class=BasicFleet)
    test_board.add_to_restricted_indexes([1, 2])
    test_board.add_to_restricted_indexes([1, 2])
    test_board.add_to_restricted_indexes([3, 8])
    assert [1, 2] in test_board.restricted_indexes
    assert [3, 8] in test_board.restricted_indexes
    assert not ([2, 1] in test_board.restricted_indexes)
    # make sure duplicates are not added
    assert len(test_board.restricted_indexes) == 2

    # Add multiple indexes
    test_board = Board(side_length=10, fleet_class=BasicFleet)
    test_board.add_to_restricted_indexes([[1, 2], [3, 1], [1, 1]])
    assert [1, 2] in test_board.restricted_indexes
    assert [3, 1] in test_board.restricted_indexes
    assert [1, 1] in test_board.restricted_indexes
    assert not ([2, 1] in test_board.restricted_indexes)


def test_get_adjacent_indexes():
    test_board = Board(side_length=10, fleet_class=BasicFleet)
    assert test_board.get_adjacent_indexes([2, 2]) == [
        [1, 1], [1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2], [3, 3]]
    assert test_board.get_adjacent_indexes([1, 2]) == [
        [1, 1], [1, 3], [2, 1], [2, 2], [2, 3]]
    assert test_board.get_adjacent_indexes([1, 10]) == [
        [1, 9], [2, 9], [2, 10]]
    assert test_board.get_adjacent_indexes([10, 10]) == [
        [9, 9], [9, 10], [10, 9]]


def test_shoot_at_index():
    test_board = Board(side_length=10, fleet_class=BasicFleet)
    ship1 = Destroyer()
    ship2 = Destroyer()
    test_board.add_ship_to_board(ship=ship1, index=[1, 1], orientation=Orientation.Right)
    test_board.add_ship_to_board(ship=ship2, index=[3, 1], orientation=Orientation.Right)

    test_board.shoot_at_index(index=[1, 1])
    # Shooting will set the target shot_at
    assert test_board.get_element_of_index(index=[1, 1]).shot_at is True
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
    test_board = Board(side_length=10, fleet_class=BasicFleet)
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

    test_board = Board(side_length=10, fleet_class=BasicFleet)
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
