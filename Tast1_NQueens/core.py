"""N-Queens: board verification and Min-Conflicts (educational reference)."""
from __future__ import annotations
from dataclasses import dataclass
import random
from time import perf_counter


def verify_solution(queens: list[int] | None, n: int) -> bool:
    """Queens indexed by column; value is the queen's row."""
    if queens is None or len(queens) != n or any(not isinstance(r, int) or r < 0 or r >= n for r in queens):
        return False
    return (len(set(queens)) == n
            and len({r - c for c, r in enumerate(queens)}) == n
            and len({r + c for c, r in enumerate(queens)}) == n)


@dataclass
class LocalResult:
    queens: list[int] | None
    success: bool
    steps: int
    restarts: int
    elapsed_ms: float
    strategy: str


class MinConflictsSolver:
    """A queen in every column. Row and diagonal counts maintained incrementally."""
    def __init__(self, n: int, strategy: str = 'standard', max_steps: int | None = None,
                 max_restarts: int = 15, seed: int | None = None):
        if n < 1:
            raise ValueError('N must be positive')
        if strategy not in ('standard', 'most_conflicted'):
            raise ValueError('Unrecognized strategy')
        self.n, self.strategy = n, strategy
        self.max_steps = max_steps if max_steps is not None else max(500, n * 30)
        self.max_restarts = max_restarts
        self.rng = random.Random(seed)

    def solve(self) -> LocalResult:
        n = self.n
        t0 = perf_counter()
        if n in (2, 3):
            return LocalResult(None, False, 0, 0, (perf_counter()-t0)*1000, self.strategy)
        steps_total = 0
        for restart in range(self.max_restarts + 1):
            # Same random initial state given the same seed; later choices differ.
            queens = [self.rng.randrange(n) for _ in range(n)]
            row_count = [0] * n
            diag_a = [0] * (2*n-1)   # row - col + n - 1
            diag_b = [0] * (2*n-1)   # row + col
            for c, r in enumerate(queens):
                row_count[r] += 1
                diag_a[r-c+n-1] += 1
                diag_b[r+c] += 1

            for _ in range(self.max_steps):
                conflicted = []
                worst = 0
                for c, r in enumerate(queens):
                    conflicts = row_count[r] + diag_a[r-c+n-1] + diag_b[r+c] - 3
                    if conflicts > 0:
                        if self.strategy == 'standard':
                            conflicted.append(c)
                        elif conflicts > worst:
                            worst = conflicts
                            conflicted = [c]
                        elif conflicts == worst:
                            conflicted.append(c)
                if not conflicted:
                    assert verify_solution(queens, n)
                    return LocalResult(queens, True, steps_total, restart,
                                       (perf_counter()-t0)*1000, self.strategy)

                col = self.rng.choice(conflicted)
                old_row = queens[col]
                row_count[old_row] -= 1
                diag_a[old_row-col+n-1] -= 1
                diag_b[old_row+col] -= 1
                best_score = n * 3 + 1
                best_rows = []
                for r in range(n):
                    score = row_count[r] + diag_a[r-col+n-1] + diag_b[r+col]
                    if score < best_score:
                        best_score = score
                        best_rows = [r]
                    elif score == best_score:
                        best_rows.append(r)
                new_row = self.rng.choice(best_rows)
                queens[col] = new_row
                row_count[new_row] += 1
                diag_a[new_row-col+n-1] += 1
                diag_b[new_row+col] += 1
                steps_total += 1
        return LocalResult(None, False, steps_total, self.max_restarts,
                           (perf_counter()-t0)*1000, self.strategy)
