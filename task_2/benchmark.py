"""Small reproducible comparisons; results stay in memory/stdout by default."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "task_2"

from dataclasses import asdict, dataclass, replace
from statistics import mean, pstdev
from threading import Event
from time import perf_counter

from task_2.search.agents import CONFIGURATIONS
from task_2.core.rules import GameRules
from task_2.search.algorithms import SearchConfig, Searcher
from task_2.core.state import Base, Direction, GameState, Tank, Wall


@dataclass
class Comparison:
    suite: str
    mode: str
    mean_ms: float
    std_ms: float
    mean_nodes: float
    mean_depth: float
    timeouts: int
    fallbacks: int
    samples: int


def endgames():
    # Same states for all modes, no nemesis. Natural final-turn rule keeps
    # terminal-only minimax measurable; no artificial zero-valued cutoff.
    return [
        GameState(
            7,
            5,
            (Tank(0, 2, 2, Direction.RIGHT, 0), Tank(1, 4, 2, Direction.LEFT, 1)),
            (Base(0, 0, 4), Base(1, 6, 4)),
            max_turns=1,
        ),
        GameState(
            7,
            5,
            (Tank(0, 2, 2, Direction.RIGHT, 0), Tank(1, 5, 1, Direction.LEFT, 1)),
            (Base(0, 0, 4), Base(1, 6, 2, 1)),
            (Wall(3, 2, 1),),
            max_turns=1,
        ),
    ]


def compare(state=None, budget_ms=150, depth=3, repeats=3, cancel_event=None):
    """Fixed one-turn endgames + same budget per sampled tank decision.

    The timed suite is a search microbenchmark, not the shared multi-agent
    match budget or a win-rate tournament. Timed-out samples remain in stats.
    """
    cancel_event = cancel_event or Event()
    rules = GameRules()
    current = state or replace(endgames()[0], max_turns=300)
    rows = []
    for suite, scenarios in [("terminal", endgames()), ("budget", [current])]:
        for mode, (alpha_beta, heuristic) in CONFIGURATIONS.items():
            results = []
            for _ in range(repeats):
                for scenario in scenarios:
                    if cancel_event.is_set():
                        return rows
                    # Single fixed horizon when comparing algorithms. Under a
                    # deadline use iterative deepening for usable partial work.
                    config = SearchConfig(
                        1 if suite == "terminal" else depth,
                        alpha_beta,
                        heuristic,
                        suite == "budget",
                    )
                    deadline = (
                        None
                        if suite == "terminal"
                        else perf_counter() + budget_ms / 1000
                    )
                    result = Searcher(rules, config).choose(
                        scenario,
                        scenario.alive[0].id,
                        deadline=deadline,
                        cancel_event=cancel_event,
                    )
                    results.append(result.stats)
            timings = [s.elapsed_seconds * 1000 for s in results]
            rows.append(
                Comparison(
                    suite,
                    mode,
                    mean(timings),
                    pstdev(timings),
                    mean(s.nodes for s in results),
                    mean(s.completed_depth for s in results),
                    sum(s.timed_out for s in results),
                    sum(s.completed_depth == 0 for s in results),
                    len(results),
                )
            )
    return rows


if __name__ == "__main__":
    import json

    print(json.dumps([asdict(row) for row in compare()], indent=2))
