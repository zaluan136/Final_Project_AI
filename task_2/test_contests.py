"""Run from the project root: python -m unittest task_2.test_contests."""

import unittest
from collections import Counter

from task_2.core.state import Action, Base, Direction, GameState, Tank
from task_2.core.rules import GameRules
from task_2.match.runner import MatchRunner


class ContestBot:
    def __init__(self, tank_id, action):
        self.tank_id, self.action = tank_id, action

    def choose_action(self, state, draft, deadline=None):
        legal = GameRules().actions(state, self.tank_id, draft)
        return self.action if self.action in legal else Action.STAY


class ContestTests(unittest.TestCase):
    def scenario(self, count=2, teammates=False):
        positions = [
            (1, 2, Direction.RIGHT, Action.MOVE_RIGHT),
            (3, 2, Direction.LEFT, Action.MOVE_LEFT),
            (2, 1, Direction.DOWN, Action.MOVE_DOWN),
            (2, 3, Direction.UP, Action.MOVE_UP),
        ]
        tanks = tuple(
            Tank(i, x, y, direction, (0 if i < 2 else 1) if teammates else i % 2)
            for i, (x, y, direction, _) in enumerate(positions[:count])
        )
        state = GameState(5, 5, tanks, (Base(0, 0, 0), Base(1, 4, 4)))
        actions = {i: p[3] for i, p in enumerate(positions[:count])}
        return state, actions

    def test_equal_probabilities_for_two_three_four(self):
        rules = GameRules()
        for count in (2, 3, 4):
            state, actions = self.scenario(count)
            outcomes = rules.resolve(state, rules.begin(state), actions)
            self.assertEqual(len(outcomes), count)
            for probability, draft in outcomes:
                self.assertAlmostEqual(probability, 1 / count)
                self.assertEqual(len(draft.pending), count - 1)

    def test_human_can_win_or_lose_and_retry(self):
        for count, teammates in ((2, False), (3, True), (4, False)):
            wins = Counter()
            for seed in range(100):
                state, actions = self.scenario(count, teammates)
                bots = {i: ContestBot(i, action) for i, action in actions.items()}
                runner = MatchRunner(
                    state, bots, seed=seed, player_priority_enabled=False
                )
                runner.control(0)
                runner.resume()
                # Exercise the UI's flow: bots may finish thinking before input.
                runner.collect()
                self.assertEqual(runner.state.turn, 0)
                self.assertIn(0, runner.draft.pending)
                runner.submit(actions[0])
                runner.collect()
                won = 0 in dict(runner.draft.accepted)
                wins[won] += 1
                if not won:
                    self.assertIn(0, runner.draft.pending)
                    self.assertNotIn(actions[0], runner.human_options())
                    runner.submit(Action.STAY)
                    runner.collect()
                self.assertTrue(runner.ready)
                runner.commit()
                self.assertEqual(runner.state.turn, 1)
                self.assertEqual(
                    (runner.state.tank(0).x, runner.state.tank(0).y),
                    (2, 2) if won else (1, 2),
                )
                self.assertEqual(
                    sum((t.x, t.y) == (2, 2) for t in runner.state.alive), 1
                )
            self.assertGreater(wins[True], 0)
            self.assertGreater(wins[False], 0)

    def test_controlled_tank_priority_and_toggle(self):
        for count in (2, 3, 4):
            for human in range(count):
                state, actions = self.scenario(count)
                bots = {i: ContestBot(i, a) for i, a in actions.items()}
                runner = MatchRunner(state, bots, seed=0)
                runner.control(human)
                proposals = dict(reversed(list(actions.items())))
                outcomes = runner.rules.resolve(state, runner.draft, proposals)
                self.assertEqual(len(outcomes), 1)
                self.assertEqual(outcomes[0][0], 1)
                self.assertEqual(dict(outcomes[0][1].accepted), {human: actions[human]})
                runner.resume()
                runner.submit(actions[human])
                runner.collect()
                self.assertTrue(runner.ready)
                runner.commit()
                self.assertEqual(
                    (runner.state.tank(human).x, runner.state.tank(human).y), (2, 2)
                )
                runner.set_player_priority(False)
                self.assertIsNone(runner.rules.priority_tank)
                fair = runner.rules.resolve(state, runner.rules.begin(state), actions)
                self.assertEqual(len(fair), count)
                runner.set_player_priority(True)
                runner.control(None)
                self.assertIsNone(runner.rules.priority_tank)


if __name__ == "__main__":
    unittest.main()
