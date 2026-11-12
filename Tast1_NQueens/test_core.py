"""Unit tests independent of the optional PySAT dependency."""
import unittest
from core import verify_solution, MinConflictsSolver
from sat import square_var


class TestNQueens(unittest.TestCase):
    def test_var_numbers(self):
        self.assertEqual(square_var(4,0,0),1)
        self.assertEqual(square_var(4,3,3),16)
        self.assertEqual(len({square_var(8,r,c) for r in range(8) for c in range(8)}),64)

    def test_validator(self):
        self.assertTrue(verify_solution([2,0,3,1],4))
        self.assertFalse(verify_solution([0,0,2,3],4))
        self.assertFalse(verify_solution([0,1,2,3],4))
        self.assertFalse(verify_solution(None,4))

    def test_local_for_standard_and_heuristic(self):
        for method in ('standard','most_conflicted'):
            for n in (4,8,12,20):
                result=MinConflictsSolver(n,method,seed=345,max_steps=5000,max_restarts=50).solve()
                self.assertTrue(result.success,(n,method,result))
                self.assertTrue(verify_solution(result.queens,n))

    def test_unsatisfiable(self):
        for method in ('standard','most_conflicted'):
            self.assertFalse(MinConflictsSolver(2,method).solve().success)
            self.assertFalse(MinConflictsSolver(3,method).solve().success)


if __name__=='__main__':
    unittest.main()
