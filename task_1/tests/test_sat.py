import unittest

from task_1.core import verify_solution
from task_1.experiments import local_experiments, sat_experiments
from task_1.sat import SATSolver


class SATTests(unittest.TestCase):
    def test_encodings_find_valid_solutions_and_unsatisfiable_boards(self):
        for encoding in ("pairwise", "seqcounter", "ladder"):
            for n in (2, 3, 4, 8):
                with self.subTest(encoding=encoding, n=n):
                    result = SATSolver(n, encoding).solve()
                    self.assertEqual(result.success, n >= 4)
                    if result.success:
                        self.assertTrue(verify_solution(result.queens, n))
                    self.assertGreaterEqual(result.solve_ms, 0)

    def test_pairwise_clause_counts(self):
        for n, expected in ((4, 80), (8, 736), (12, 2608)):
            self.assertEqual(SATSolver(n).solve().cnf.num_clauses, expected)

    def test_experiments_include_required_metrics(self):
        sat = sat_experiments(ns=(4, 8), methods=("pairwise",), trials=2)
        self.assertEqual([row.n for row in sat], [4, 8])
        self.assertTrue(
            all(
                row.successful == 2 and row.clauses and row.solve_ms is not None
                for row in sat
            )
        )
        local = local_experiments(ns=(4, 8), trials=2)
        self.assertEqual({row.method for row in local}, {"standard", "most_conflicted"})
        self.assertTrue(
            all(row.trials == 2 and row.mean_steps is not None for row in local)
        )


if __name__ == "__main__":
    unittest.main()
