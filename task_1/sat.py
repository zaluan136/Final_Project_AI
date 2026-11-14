"""Propositional N-Queens encoding using python-sat's Glucose3 and CardEnc.

Every physical square is represented by one propositional variable.
At-most-one groups are encoded with the selected cardinality encoding.
"""

from __future__ import annotations
from dataclasses import dataclass
from time import perf_counter
from .core import verify_solution


def square_var(n: int, row: int, col: int) -> int:
    return row * n + col + 1


@dataclass
class CNFInfo:
    n: int
    encoding: str
    clauses: list[list[int]]
    num_vars: int
    build_ms: float
    symmetry: bool

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)


@dataclass
class SATResult:
    queens: list[int] | None
    success: bool
    cnf: CNFInfo
    setup_ms: float
    solve_ms: float


class CNFEncoder:
    ENCODINGS = {"pairwise", "seqcounter", "ladder"}

    def __init__(self, n: int, encoding: str = "pairwise", symmetry: bool = False):
        if n < 1:
            raise ValueError("N must be positive")
        if encoding not in self.ENCODINGS:
            raise ValueError(f"Unknown encoding: {encoding}")
        self.n, self.encoding, self.symmetry = n, encoding, symmetry

    def encode(self) -> CNFInfo:
        try:
            from pysat.card import CardEnc, EncType
            from pysat.formula import IDPool
        except ImportError as exc:
            raise RuntimeError(
                "Install python-sat: python -m pip install -r requirements.txt"
            ) from exc
        start = perf_counter()
        n = self.n
        pool = IDPool(start_from=n * n + 1)
        clauses: list[list[int]] = []
        encoding_id = {
            "pairwise": EncType.pairwise,
            "seqcounter": EncType.seqcounter,
            "ladder": EncType.ladder,
        }[self.encoding]

        def at_most_one(group: list[int]):
            if len(group) >= 2:
                encoding = CardEnc.atmost(
                    lits=group, bound=1, vpool=pool, encoding=encoding_id
                )
                clauses.extend(encoding.clauses)

        # Build all constraint scopes in one pass over the board.
        # This avoids rescanning all N² squares for each of the O(N) diagonals.
        rows = [[] for _ in range(n)]
        columns = [[] for _ in range(n)]
        diag_down = [[] for _ in range(2*n-1)]
        diag_up = [[] for _ in range(2*n-1)]
        for r in range(n):
            for c in range(n):
                var = square_var(n, r, c)
                rows[r].append(var)
                columns[c].append(var)
                diag_down[r-c+n-1].append(var)
                diag_up[r+c].append(var)

        # Exactly one queen per row: at least one, plus at most one.
        for group in rows:
            clauses.append(group)
            at_most_one(group)

        # At most one per column; N row queens then imply exactly one per column.
        for group in columns:
            at_most_one(group)

        # No two queens may share either diagonal direction.
        for group in (*diag_down, *diag_up):
            at_most_one(group)

        if self.symmetry and n >= 2:
            # Reflect columns: at least one solution has the first-row queen
            # in the left half (center included if odd). Not for model counting.
            clauses.append([square_var(n, 0, c) for c in range((n + 1) // 2)])

        return CNFInfo(
            n,
            self.encoding,
            clauses,
            max(n * n, pool.top),
            (perf_counter() - start) * 1000,
            self.symmetry,
        )


class SATSolver:
    def __init__(self, n: int, encoding: str = "pairwise", symmetry: bool = False):
        self.encoder = CNFEncoder(n, encoding, symmetry)

    def solve(self) -> SATResult:
        try:
            from pysat.solvers import Glucose3
        except ImportError as exc:
            raise RuntimeError(
                "Install python-sat: python -m pip install -r requirements.txt"
            ) from exc
        cnf = self.encoder.encode()
        t0 = perf_counter()
        with Glucose3(bootstrap_with=cnf.clauses) as solver:
            setup_ms = (perf_counter() - t0) * 1000
            t1 = perf_counter()
            satisfiable = solver.solve()
            solve_ms = (perf_counter() - t1) * 1000
            model = solver.get_model() if satisfiable else None
        queens = None
        if model is not None:
            selected = set(x for x in model if x > 0 and x <= cnf.n * cnf.n)
            queens = [-1] * cnf.n
            for r in range(cnf.n):
                for c in range(cnf.n):
                    if square_var(cnf.n, r, c) in selected:
                        queens[c] = r
            if not verify_solution(queens, cnf.n):
                raise AssertionError("Solver returned a model with invalid queens")
        return SATResult(queens, bool(satisfiable), cnf, setup_ms, solve_ms)
