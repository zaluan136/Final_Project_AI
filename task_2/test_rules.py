import unittest
from dataclasses import replace

from task_2.core.rules import Draft, GameRules
from task_2.core.state import Action, Base, Bullet, Direction, GameState, Tank, Wall
from task_2.search.evaluation import terminal_value


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.rules = GameRules()
        self.state = GameState(
            9,
            5,
            (Tank(0, 1, 2, Direction.RIGHT, 0), Tank(1, 7, 2, Direction.LEFT, 1)),
            (Base(0, 0, 0), Base(1, 8, 4)),
        )

    def execute(self, state, actions):
        return self.rules.execute(state, Draft(tuple(sorted(actions.items()))))

    def test_any_tank_destroyed_ends_even_with_teammate(self):
        state = replace(
            self.state,
            tanks=(
                replace(self.state.tanks[0], hp=0),
                Tank(2, 1, 3, Direction.UP, 0),
                self.state.tanks[1],
            ),
        )
        result = self.rules.outcome(state)
        self.assertEqual((result.winner, result.reason), (1, "tank_destroyed"))
        self.assertEqual(terminal_value(result, 0), -100000)
        self.assertEqual(terminal_value(result, 1), 100000)

    def test_simultaneous_destruction_is_draw(self):
        state = replace(
            self.state,
            tanks=(
                replace(self.state.tanks[0], hp=1),
                replace(self.state.tanks[1], hp=1),
            ),
            bullets=(Bullet(0, 2, Direction.RIGHT, 1), Bullet(8, 2, Direction.LEFT, 0)),
        )
        result = self.execute(state, {0: Action.STAY, 1: Action.STAY})
        self.assertEqual(self.rules.outcome(result).winner, None)
        self.assertEqual(self.rules.outcome(result).reason, "mutual_destruction")

    def test_base_destroyed_ends_game(self):
        state = replace(
            self.state, bases=(self.state.bases[0], replace(self.state.bases[1], hp=0))
        )
        self.assertEqual(
            (self.rules.outcome(state).winner, self.rules.outcome(state).reason),
            (0, "base_destroyed"),
        )

    def test_bullets_travel_three_cells_and_stop_at_first_obstacle(self):
        state = replace(self.state, walls=(Wall(3, 2),))
        result = self.execute(state, {0: Action.FIRE, 1: Action.STAY})
        self.assertEqual(result.walls[0].hp, 2)
        self.assertFalse(result.bullets)
        result = self.execute(self.state, {0: Action.FIRE, 1: Action.STAY})
        self.assertEqual([(b.x, b.y) for b in result.bullets], [(4, 2)])
        result = self.execute(result, {0: Action.STAY, 1: Action.STAY})
        self.assertEqual(result.tank(1).hp, 5)
        self.assertFalse(result.bullets)

    def test_bullet_stops_on_killing_hit(self):
        state = replace(
            self.state,
            tanks=(self.state.tanks[0], replace(self.state.tanks[1], x=3, hp=1)),
        )
        result = self.execute(state, {0: Action.FIRE, 1: Action.STAY})
        self.assertEqual(result.tank(1).hp, 0)
        self.assertFalse(result.bullets)
        self.assertEqual(self.rules.outcome(result).winner, 0)

    def test_bullet_hits_base_and_stops_at_board_edge(self):
        state = replace(self.state, bases=(self.state.bases[0], Base(1, 4, 2, 1)))
        result = self.execute(state, {0: Action.FIRE, 1: Action.STAY})
        self.assertEqual(result.bases[1].hp, 0)
        self.assertEqual(self.rules.outcome(result).winner, 0)
        self.assertFalse(result.bullets)
        state = replace(self.state, bullets=(Bullet(8, 3, Direction.RIGHT, 0),))
        result = self.execute(state, {0: Action.STAY, 1: Action.STAY})
        self.assertFalse(result.bullets)

    def test_movement_and_initial_hp(self):
        self.assertEqual(
            (self.state.tank(0).hp, self.state.bases[0].hp, Wall(4, 4).hp), (6, 9, 3)
        )
        result = self.execute(self.state, {0: Action.MOVE_UP, 1: Action.STAY})
        self.assertEqual(
            (result.tank(0).x, result.tank(0).y, result.tank(0).direction),
            (1, 1, Direction.UP),
        )
        self.assertEqual(len(Action), 6)


if __name__ == "__main__":
    unittest.main()
