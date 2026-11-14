from dataclasses import dataclass, replace
from time import perf_counter

from .model import KakuroCSP


@dataclass
class Statistics:
    branches: int = 0
    backtracks: int = 0
    pruned: int = 0
    elapsed: float = 0.0


@dataclass(frozen=True)
class SolverEvent:
    kind: str
    cell: tuple[int, int] | None
    message: str
    assignment: dict
    domains: dict
    statistics: Statistics


class KakuroSolver:
    def __init__(self, board):
        self.csp = KakuroCSP(board)
        self.assignment = {}
        self.domains = self.csp.initial_domains()
        self.statistics = Statistics()
        self.solution = None
        self._started = False

    def event(self, kind, cell, message):
        return SolverEvent(
            kind,
            cell,
            message,
            dict(self.assignment),
            {key: frozenset(value) for key, value in self.domains.items()},
            replace(self.statistics),
        )

    def select_variable(self):
        remaining = set(self.domains) - self.assignment.keys()
        return min(
            remaining,
            key=lambda cell: (
                len(self.domains[cell]),
                -len(self.csp.neighbors[cell] & remaining),
                cell,
            ),
        )

    def order_values(self, cell):
        scores = []
        for value in sorted(self.domains[cell]):
            if not self.csp.consistent(cell, value, self.assignment, self.domains):
                continue
            trial = dict(self.assignment)
            trial[cell] = value
            removed = sum(
                not self.csp.consistent(other, candidate, trial, self.domains)
                for other in sorted(self.csp.neighbors[cell])
                if other not in trial
                for candidate in self.domains[other]
            )
            scores.append((removed, value))
        return [value for _, value in sorted(scores)]

    def forward_check(self, cell):
        for other in sorted(self.csp.neighbors[cell]):
            if other in self.assignment:
                continue
            removed = {
                value
                for value in self.domains[other]
                if not self.csp.consistent(other, value, self.assignment, self.domains)
            }
            if removed:
                before = sorted(self.domains[other])
                self.domains[other] -= removed
                self.statistics.pruned += len(removed)
                labels = "; ".join(run.label for run in self.csp.board.cell_runs[other])
                yield self.event(
                    "prune",
                    other,
                    f"After R{cell[0] + 1}C{cell[1] + 1}={self.assignment[cell]}, "
                    f"domain {before} → {sorted(self.domains[other])}. "
                    f"Removed {sorted(removed)}: duplicate or unattainable sum. "
                    f"Runs: {labels}.",
                )
            if not self.domains[other]:
                yield self.event("failure", other, "Domain is empty; this branch fails.")
                return False
        return True

    def backtrack(self):
        if len(self.assignment) == len(self.domains):
            return self.csp.is_solution(self.assignment)
        cell = self.select_variable()
        values = self.order_values(cell)
        remaining = set(self.domains) - self.assignment.keys()
        degree = len(self.csp.neighbors[cell] & remaining)
        yield self.event(
            "select",
            cell,
            f"MRV + Degree selected domain {sorted(self.domains[cell])} "
            f"with {degree} unassigned neighbors. LCV order: {values}.",
        )
        for value in values:
            saved = {key: set(domain) for key, domain in self.domains.items()}
            self.statistics.branches += 1
            self.assignment[cell] = value
            self.domains[cell] = {value}
            yield self.event(
                "try", cell, f"Try {value}, then check neighboring domains."
            )
            valid = yield from self.forward_check(cell)
            if valid and (yield from self.backtrack()):
                return True
            self.assignment.pop(cell)
            self.domains = saved
            self.statistics.backtracks += 1
            yield self.event(
                "restore",
                cell,
                f"Value {value} failed. Restore the previous domains "
                "and try the next value, if available.",
            )
        yield self.event("failure", cell, "No valid values remain for this cell.")
        return False

    def search(self):
        yield self.event(
            "start",
            None,
            "Initialize domains to 1–9; begin backtracking with forward checking.",
        )
        if any(not domain for domain in self.domains.values()) or any(
            not self.csp.run_possible(run, self.assignment, self.domains)
            for run in self.csp.board.runs
        ):
            yield self.event(
                "failure", None, "An empty domain or impossible clue prevents a solution."
            )
            solved = False
        else:
            solved = yield from self.backtrack()
        self.solution = dict(self.assignment) if solved else None
        yield self.event(
            "complete",
            None,
            "A valid solution was found." if solved else "No solution was found.",
        )

    def events(self):
        if self._started:
            raise RuntimeError("Create a new solver before starting another search")
        self._started = True
        iterator = self.search()
        while True:
            start = perf_counter()
            try:
                event = next(iterator)
            except StopIteration:
                self.statistics.elapsed += perf_counter() - start
                return
            self.statistics.elapsed += perf_counter() - start
            yield replace(event, statistics=replace(self.statistics))

    def solve(self):
        for _ in self.events():
            pass
        return self.solution
