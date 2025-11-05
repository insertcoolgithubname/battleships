from battleships import Board, BasicFleet, Destroyer, Orientation


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
