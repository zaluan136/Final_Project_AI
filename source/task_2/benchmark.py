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
from task_2.search.tactics import route


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
    mean_expanded_nodes: float = 0
    std_expanded_nodes: float = 0
    std_depth: float = 0


def endgames():
    # One-turn scenarios allow terminal-only search to finish.
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


def compare(state=None, budget_ms=150, depth=3, repeats=10, cancel_event=None):
    """Repeated per-decision comparisons, not complete match tournaments.

    Every sample starts from the same immutable state. Rotate method order,
    clear route caches, and use identical tactical ordering with no memory,
    nemesis or player-priority advantage. Counts include work in unfinished
    iterative-deepening passes. Return no chart rows if cancelled.
    """
    if type(repeats) is not int or repeats < 1:
        raise ValueError("Repeats must be a positive integer")
    if type(budget_ms) is not int or budget_ms < 1:
        raise ValueError("Budget must be a positive integer in ms")
    SearchConfig(depth)
    cancel_event = cancel_event or Event()
    rules = GameRules()
    current = state or replace(endgames()[0], max_turns=300)
    current.validate_ready()
    if rules.outcome(current) is not None:
        raise ValueError("Compare requires a nonterminal decision snapshot")
    modes = list(CONFIGURATIONS)
    rows = []
    for suite, scenarios in [("terminal", endgames()), ("budget", [current])]:
        results = {mode: [] for mode in modes}
        for repeat in range(repeats):
            offset = repeat % len(modes)
            order = modes[offset:] + modes[:offset]
            for scenario in scenarios:
                for mode in order:
                    if cancel_event.is_set():
                        return []
                    alpha_beta, heuristic = CONFIGURATIONS[mode]
                    route.cache_clear()
                    config = SearchConfig(1 if suite == "terminal" else depth,
                                          alpha_beta, heuristic, suite == "budget")
                    deadline = None if suite == "terminal" else perf_counter()+budget_ms/1000
                    result = Searcher(rules, config).choose(
                        scenario, scenario.alive[0].id, deadline=deadline,
                        cancel_event=cancel_event)
                    if cancel_event.is_set():
                        return []
                    results[mode].append(result.stats)
        for mode in modes:
            stats = results[mode]
            timings = [s.elapsed_seconds*1000 for s in stats]
            rows.append(Comparison(
                suite=suite, mode=mode, mean_ms=mean(timings), std_ms=pstdev(timings),
                mean_nodes=mean(s.nodes for s in stats),
                mean_depth=mean(s.completed_depth for s in stats),
                timeouts=sum(s.timed_out for s in stats),
                fallbacks=sum(s.completed_depth == 0 for s in stats),
                samples=len(stats),
                mean_expanded_nodes=mean(s.expanded_nodes for s in stats),
                std_expanded_nodes=pstdev(s.expanded_nodes for s in stats),
                std_depth=pstdev(s.completed_depth for s in stats)))
    return rows


if __name__ == "__main__":
    import json

    print(json.dumps([asdict(row) for row in compare()], indent=2))


