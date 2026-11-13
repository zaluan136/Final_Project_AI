"""Reproducible benchmarks for SAT and Min-Conflicts."""

from __future__ import annotations
import csv
from dataclasses import asdict, dataclass
from statistics import mean, median
from .core import MinConflictsSolver
from .sat import SATSolver


@dataclass
class ExperimentRow:
    family: str
    n: int
    method: str
    trials: int
    successful: int
    variables: int | None
    clauses: int | None
    build_ms: float | None
    setup_ms: float | None
    solve_ms: float | None
    total_ms: float
    mean_steps: float | None
    median_ms: float


def sat_experiments(
    ns=(4, 8, 12, 20),
    methods=("pairwise", "seqcounter", "ladder"),
    trials=3,
    symmetry=False,
):
    out = []
    for n in ns:
        for method in methods:
            results = [SATSolver(n, method, symmetry).solve() for _ in range(trials)]
            elapsed = [x.cnf.build_ms + x.setup_ms + x.solve_ms for x in results]
            out.append(
                ExperimentRow(
                    "SAT",
                    n,
                    method + (" + symmetry" if symmetry else ""),
                    trials,
                    sum(r.success for r in results),
                    results[0].cnf.num_vars,
                    results[0].cnf.num_clauses,
                    round(mean(r.cnf.build_ms for r in results), 4),
                    round(mean(r.setup_ms for r in results), 4),
                    round(mean(r.solve_ms for r in results), 4),
                    round(mean(elapsed), 4),
                    None,
                    round(median(elapsed), 4),
                )
            )
    return out


def local_experiments(ns=(8, 20, 50, 100), trials=10, max_restarts=15):
    out = []
    for n in ns:
        for method in ("standard", "most_conflicted"):
            results = [
                MinConflictsSolver(
                    n, method, max_restarts=max_restarts, seed=9000 + i
                ).solve()
                for i in range(trials)
            ]
            times = [r.elapsed_ms for r in results]
            out.append(
                ExperimentRow(
                    "LOCAL",
                    n,
                    method,
                    trials,
                    sum(r.success for r in results),
                    None,
                    None,
                    None,
                    None,
                    None,
                    round(mean(times), 4),
                    round(mean(r.steps for r in results), 2),
                    round(median(times), 4),
                )
            )
    return out


def export_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(ExperimentRow.__dataclass_fields__)
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
