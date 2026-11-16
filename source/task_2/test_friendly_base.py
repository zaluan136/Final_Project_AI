import unittest
from dataclasses import replace
from task_2.core.state import Action, Base, Bullet, Direction, GameState, Tank, Wall
from task_2.core.rules import GameRules
from task_2.match.runner import MatchRunner
from task_2.search.tactics import base_threats


class FriendlyBaseTests(unittest.TestCase):
    def setUp(self):
        self.rules = GameRules()
        self.state = GameState(
            9,
            7,
            (Tank(0, 2, 3, Direction.LEFT, 0), Tank(1, 6, 5, Direction.UP, 1)),
            (Base(0, 0, 3), Base(1, 8, 3)),
        )

    def test_direct_fire_is_illegal_for_bots_and_player(self):
        self.assertNotIn(Action.FIRE, self.rules.actions(self.state, 0))
        with self.assertRaises(ValueError):
            self.rules.resolve(
                self.state,
                self.rules.begin(self.state),
                {0: Action.FIRE, 1: Action.STAY},
            )
        runner = MatchRunner(self.state)
        runner.control(0)
        self.assertNotIn(Action.FIRE, runner.human_options())
        with self.assertRaises(ValueError):
            runner.submit(Action.FIRE)

    def test_wall_can_be_destroyed_without_hurting_own_base(self):
        state = replace(self.state, walls=(Wall(1, 3, 1),))
        self.assertIn(Action.FIRE, self.rules.actions(state, 0))
        draft = self.rules.resolve(
            state, self.rules.begin(state), {0: Action.FIRE, 1: Action.STAY}
        )[0][1]
        after = self.rules.execute(state, draft)
        self.assertFalse(after.walls)
        self.assertEqual(after.bases[0].hp, 9)
        self.assertNotIn(Action.FIRE, self.rules.actions(after, 0))

    def test_friendly_base_absorbs_existing_bullets(self):
        for owner, hp in ((0, 9), (1, 8)):
            bullet = Bullet(0, 3, Direction.LEFT, owner)
            after = self.rules._collisions(self.state, (bullet,))
            self.assertEqual(after.bases[0].hp, hp)
            self.assertFalse(after.bullets)
        friendly = replace(self.state, bullets=(Bullet(1, 3, Direction.LEFT, 0),))
        self.assertFalse(base_threats(friendly, 0)[1])
        enemy = replace(friendly, bullets=(Bullet(1, 3, Direction.LEFT, 1),))
        self.assertTrue(base_threats(enemy, 0)[1])

    def test_enemy_base_and_friendly_tanks_still_take_damage(self):
        state = replace(
            self.state,
            tanks=(
                replace(self.state.tanks[0], x=6, direction=Direction.RIGHT),
                self.state.tanks[1],
            ),
        )
        draft = self.rules.resolve(
            state, self.rules.begin(state), {0: Action.FIRE, 1: Action.STAY}
        )[0][1]
        after = self.rules.execute(state, draft)
        self.assertEqual(after.bases[1].hp, 8)
        after = self.rules._collisions(state, (Bullet(6, 3, Direction.RIGHT, 0),))
        self.assertEqual(after.tank(0).hp, 5)


if __name__ == "__main__":
    unittest.main()
