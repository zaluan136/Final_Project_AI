import tempfile
import unittest
from pathlib import Path
from time import perf_counter

from task_2.benchmark import compare
from task_2.core.state import Action, Base, Direction, GameState, Tank
from task_2.match.bot_loader import FileAgent
from task_2.match.runner import MatchConfig, MatchRunner


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(
            5,
            5,
            (Tank(0, 1, 1, Direction.RIGHT, 0), Tank(1, 3, 3, Direction.LEFT, 1)),
            (Base(0, 0, 0), Base(1, 4, 4)),
        )

    def test_two_external_bots_play_same_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / f"bot{i}.py" for i in range(2)]
            paths[0].write_text(
                'def choose_action(state, tank_id, draft, deadline):\n    return "MOVE_RIGHT"\n',
                encoding="utf-8",
            )
            paths[1].write_text(
                'def choose_action(state, tank_id, draft, deadline):\n    return "STAY"\n',
                encoding="utf-8",
            )
            agents = {i: FileAgent(path, i) for i, path in enumerate(paths)}
            runner = MatchRunner(self.state, agents, MatchConfig(True, 10000), seed=1)
            runner.collect()
            self.assertTrue(runner.ready)
            runner.commit()
            self.assertEqual(
                runner.last_actions, {0: Action.MOVE_RIGHT, 1: Action.STAY}
            )
            self.assertEqual((runner.state.tank(0).x, runner.state.tank(0).y), (2, 1))

    def test_external_bot_error_invalid_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.py"
            path.write_text(
                'def choose_action(*args):\n    raise ValueError("oops")\n',
                encoding="utf-8",
            )
            agent = FileAgent(path, 0)
            draft = MatchRunner(self.state).draft
            with self.assertRaises(RuntimeError):
                agent.choose_action(self.state, draft, perf_counter() + 5)
            path = Path(directory) / "invalid_bot.py"
            path.write_text(
                'def choose_action(*args):\n    return "INVALID"\n', encoding="utf-8"
            )
            agent = FileAgent(path, 0)
            with self.assertRaises((KeyError, ValueError)):
                agent.choose_action(self.state, draft, perf_counter() + 5)
            other = Path(directory) / "other_bot.py"
            other.write_text(
                'def choose_action(*args):\n    return "STAY"\n', encoding="utf-8"
            )
            runner = MatchRunner(
                self.state, {0: agent, 1: FileAgent(other, 1)}, MatchConfig(True, 10000)
            )
            runner.collect()
            self.assertTrue(runner.ready)
            runner.commit()
            self.assertIn(0, runner.last_fallback_ids)
            self.assertIn(runner.last_actions[0], tuple(Action))
            path = Path(directory) / "slow_bot.py"
            path.write_text(
                "def choose_action(*args):\n    while True: pass\n", encoding="utf-8"
            )
            agent = FileAgent(path, 0)
            with self.assertRaises(TimeoutError):
                agent.choose_action(self.state, draft, perf_counter() + 0.5)

    def test_benchmark_has_four_modes_per_suite(self):
        rows = compare(budget_ms=20, depth=1, repeats=1)
        modes = {"minimax", "alpha_beta", "heuristic_minimax", "heuristic_alpha_beta"}
        for suite in ("terminal", "budget"):
            selected = [row for row in rows if row.suite == suite]
            self.assertEqual({row.mode for row in selected}, modes)
            self.assertTrue(
                all(row.samples > 0 and row.mean_ms >= 0 for row in selected)
            )
            self.assertTrue(
                all(
                    0 <= row.fallbacks <= row.samples
                    and 0 <= row.timeouts <= row.samples
                    for row in selected
                )
            )


if __name__ == "__main__":
    unittest.main()
