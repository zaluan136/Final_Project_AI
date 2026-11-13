import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from task_3.boards import BOARDS, DEMO
from task_3.model import Board, Cell, KakuroCSP
from task_3.solver import KakuroSolver


def small_board(across=(3, 7), down=(4, 6)):
    return Board(
        "Small",
        [
            [Cell("block"), Cell("clue", down=down[0]), Cell("clue", down=down[1])],
            [Cell("clue", across=across[0]), Cell("cell"), Cell("cell")],
            [Cell("clue", across=across[1]), Cell("cell"), Cell("cell")],
        ],
    )


class SolverTests(unittest.TestCase):
    def test_boards_match_html(self):
        root = Path(__file__).resolve().parents[1] / "boards"
        for board, filename in zip(BOARDS, ("kakuro_demo.html", "kakuro_task.html")):
            text = (root / filename).read_text(encoding="utf-8")
            match = re.search(r"const grid = (\[.*?\]);", text, re.S)
            self.assertIsNotNone(match)
            if match is None:
                self.fail(f"Không tìm thấy grid trong {filename}")
            raw = match.group(1)
            raw = re.sub(r"(\w+)\s*:", r'"\1":', raw)
            raw = re.sub(r",\s*([}\]])", r"\1", raw)
            grid = json.loads(raw)
            self.assertEqual(len(grid), board.height)
            for source_row, row in zip(grid, board.grid):
                self.assertEqual(len(source_row), len(row))
                for source, cell in zip(source_row, row):
                    self.assertEqual(
                        source,
                        {
                            key: value
                            for key, value in vars(cell).items()
                            if value is not None
                        },
                    )

    def test_solutions_independent_validation_and_repeatability(self):
        for board in BOARDS:
            solutions = []
            for _ in range(3):
                solver = KakuroSolver(board)
                solution = solver.solve()
                self.assertIsNotNone(solution)
                if solution is None:
                    self.fail(f"Không tìm được lời giải cho {board.name}")
                self.assertEqual(set(solution), set(board.variables))
                self.assertTrue(
                    all(
                        type(value) is int and 1 <= value <= 9
                        for value in solution.values()
                    )
                )
                for run in board.runs:
                    values = [solution[cell] for cell in run.cells]
                    self.assertEqual(sum(values), run.total)
                    self.assertEqual(len(values), len(set(values)))
                self.assertGreater(solver.statistics.branches, 0)
                self.assertGreater(solver.statistics.pruned, 0)
                solutions.append(solution)
            self.assertTrue(all(solution == solutions[0] for solution in solutions))

    def test_restore_matches_parent_domains_and_assignments(self):
        solver = KakuroSolver(BOARDS[1])
        parents = {}
        restored = 0
        kinds = set()
        for event in solver.events():
            kinds.add(event.kind)
            depth = len(event.assignment)
            if event.kind in {"select", "restore"}:
                if event.kind == "restore":
                    assignment, domains = parents[depth]
                    self.assertEqual(event.assignment, assignment)
                    self.assertEqual(event.domains, domains)
                    restored += 1
                parents[depth] = (event.assignment, event.domains)
        self.assertGreater(restored, 0)
        self.assertTrue(
            {"start", "select", "try", "prune", "failure", "restore", "complete"}
            <= kinds
        )

    def test_unsatisfiable_restores_root(self):
        solver = KakuroSolver(small_board((3, 3), (3, 4)))
        original = solver.csp.initial_domains()
        self.assertIsNone(solver.solve())
        self.assertEqual(solver.assignment, {})
        self.assertEqual(solver.domains, original)
        self.assertGreater(solver.statistics.backtracks, 0)

    def test_empty_domain_and_impossible_clue(self):
        solver = KakuroSolver(DEMO)
        solver.domains[DEMO.variables[0]].clear()
        events = list(solver.events())
        self.assertEqual(events[-1].kind, "complete")
        self.assertIsNone(solver.solution)
        self.assertIn("failure", [event.kind for event in events])
        self.assertIsNone(KakuroSolver(small_board((50, 7))).solve())

    def test_mrv_degree_and_coordinate_ties(self):
        solver = KakuroSolver(small_board())
        self.assertEqual(solver.select_variable(), (1, 1))
        solver.domains[(2, 2)] = {4}
        self.assertEqual(solver.select_variable(), (2, 2))
        solver = KakuroSolver(DEMO)
        expected = min(
            DEMO.variables, key=lambda cell: (-len(solver.csp.neighbors[cell]), cell)
        )
        self.assertEqual(solver.select_variable(), expected)

    def test_lcv_does_not_mutate_state(self):
        solver = KakuroSolver(DEMO)
        cell = solver.select_variable()
        original = solver.csp.initial_domains()
        values = solver.order_values(cell)
        scores = []
        for value in values:
            trial = {cell: value}
            count = sum(
                not solver.csp.consistent(other, candidate, trial, original)
                for other in solver.csp.neighbors[cell]
                for candidate in original[other]
            )
            scores.append((count, value))
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(solver.domains, original)
        self.assertEqual(solver.assignment, {})

    def test_rejects_invalid_board_and_solution(self):
        with self.assertRaises(ValueError):
            Board("Empty", [])
        with self.assertRaises(ValueError):
            Board("Uncovered", [[Cell("cell")]])
        csp = KakuroCSP(small_board())
        self.assertFalse(csp.is_solution({}))
        self.assertFalse(csp.is_solution({cell: 1 for cell in csp.board.variables}))

    def test_solver_is_single_use(self):
        solver = KakuroSolver(small_board())
        solver.solve()
        with self.assertRaises(RuntimeError):
            solver.solve()

    def test_elapsed_excludes_time_between_events(self):
        clock = [0.0]

        def now():
            clock[0] += 0.001
            return clock[0]

        solver = KakuroSolver(small_board())
        with patch("task_3.solver.perf_counter", side_effect=now):
            iterator = solver.events()
            first = next(iterator)
            clock[0] += 100
            second = next(iterator)
        self.assertAlmostEqual(
            second.statistics.elapsed - first.statistics.elapsed, 0.001
        )
        iterator.close()


if __name__ == "__main__":
    unittest.main()
