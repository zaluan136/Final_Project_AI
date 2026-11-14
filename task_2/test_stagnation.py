"""Regression checks for unproductive stationary tank behaviour."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from task_2.core.state import Action, Base, Bullet, Direction, GameState, Tank, Wall
from task_2.core.rules import GameRules
from task_2.memory.memory import MovementMemory
from task_2.search.algorithms import Searcher, SearchConfig


class StagnationTests(unittest.TestCase):
    def setUp(self):
        self.rules = GameRules()
        self.state = GameState(9, 7,
            (Tank(0, 2, 2, Direction.UP, 0), Tank(1, 6, 4, Direction.DOWN, 1)),
            (Base(0, 1, 3), Base(1, 7, 3)))
        self.memory = MovementMemory(0)

    def idle(self, action=Action.STAY):
        for turn in range(1, 7):
            self.memory.observe(replace(self.state, turn=turn-1), action,
                                replace(self.state, turn=turn))

    def test_remote_bullets_do_not_disable_memory(self):
        self.idle()
        far = replace(self.state, bullets=(Bullet(8, 6, Direction.LEFT, 1),))
        self.assertGreater(self.memory.visits(far, (2, 2)), 0)
        self.assertGreater(self.memory.idle_penalty(far, self.rules, Action.STAY), 0)
        near = replace(self.state, bullets=(Bullet(0, 2, Direction.RIGHT, 1),))
        self.assertEqual(self.memory.idle_penalty(near, self.rules, Action.STAY), 0)

    def test_stationary_and_empty_shots_are_softly_demoted(self):
        self.idle(Action.FIRE)
        for action in (Action.STAY, Action.FIRE):
            self.assertGreater(self.memory.action_rank(self.state, self.rules, action), 0)
        legal = self.rules.actions(self.state, 0)
        self.assertEqual(set(self.memory.order_actions(self.state, self.rules, legal)), set(legal))
        # A shallow local maximum used to select STAY indefinitely. History
        # now offsets a small stationary advantage without banning that action.
        for alpha_beta in (False, True):
            search = Searcher(self.rules, SearchConfig(1, alpha_beta, True, False))
            with patch('task_2.search.algorithms.evaluate',
                       side_effect=lambda s, team: 10 if (s.tank(0).x, s.tank(0).y)==(2,2) else 0):
                result = search.choose(self.state, 0, memory=self.memory)
                self.assertIsNotNone(self.rules.destination(self.state, 0, result.action))
            with patch('task_2.search.algorithms.evaluate',
                       side_effect=lambda s, team: 200 if (s.tank(0).x, s.tank(0).y)==(2,2) else 0):
                result = search.choose(self.state, 0, memory=self.memory)
                self.assertIsNone(self.rules.destination(self.state, 0, result.action))

    def test_productive_shots_and_real_progress_are_preserved(self):
        self.idle()
        wall = replace(self.state, walls=(Wall(2, 1),))
        self.assertEqual(self.memory.idle_penalty(wall, self.rules, Action.FIRE), 0)
        moved = replace(self.state, turn=7,
                        tanks=(replace(self.state.tanks[0], x=3), self.state.tanks[1]))
        self.memory.observe(self.state, Action.MOVE_RIGHT, moved)
        self.assertEqual(self.memory.idle_turns, 0)

    def test_terminal_win_still_dominates(self):
        self.idle()
        state = replace(self.state,
            tanks=(replace(self.state.tanks[0], x=4, y=3, direction=Direction.RIGHT),
                   replace(self.state.tanks[1], y=5)),
            bases=(self.state.bases[0], replace(self.state.bases[1], hp=1)), max_turns=1)
        for alpha_beta, heuristic in ((False, False),(True,False),(False,True),(True,True)):
            result = Searcher(self.rules, SearchConfig(1,alpha_beta,heuristic,False)).choose(
                state, 0, memory=self.memory)
            self.assertEqual(result.action, Action.FIRE)
            self.assertEqual(result.score, 100000)


if __name__ == '__main__':
    unittest.main()
