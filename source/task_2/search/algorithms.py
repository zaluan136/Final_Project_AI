from dataclasses import dataclass
from itertools import product
from time import perf_counter
from task_2.core.state import Action
from task_2.search.evaluation import evaluate, terminal_value
from task_2.search.tactics import action_priorities


@dataclass(frozen=True)
class SearchConfig:
    depth: int = 2
    alpha_beta: bool = True
    heuristic: bool = True
    iterative_deepening: bool = True

    def __post_init__(self):
        if type(self.depth) is not int or self.depth < 1:
            raise ValueError("Positive depth required")


@dataclass
class SearchStats:
    nodes: int = 0
    expanded_nodes: int = 0  # Nonterminal MAX/MIN calls that generate action combinations.
    cutoffs: int = 0
    chance_outcomes: int = 0
    completed_depth: int = 0
    elapsed_seconds: float = 0
    timed_out: bool = False
    exact_terminal_search: bool = False


@dataclass
class SearchResult:
    action: Action | None
    score: float
    stats: SearchStats


def predicted_action(rules, s, tid, draft, memory=None):
    legal = rules.actions(s, tid, draft)
    priorities = action_priorities(s, tid, rules, legal)
    if memory is not None:
        return memory.order_actions(s, rules, legal, priorities)[0]
    return min(legal, key=priorities.get)


class Searcher:
    def __init__(self, rules, config=None):
        self.rules = rules
        self.config = config or SearchConfig()

    def choose(
        self,
        state,
        tank_id,
        draft=None,
        deadline=None,
        nemesis=None,
        cancel_event=None,
        memory=None,
    ):
        start = perf_counter()
        stats = SearchStats()
        team = state.tank(tank_id).team
        terminal = self.rules.outcome(state)
        if terminal is not None:
            return SearchResult(None, terminal_value(terminal, team), stats)
        draft = draft or self.rules.begin(state)
        if tank_id not in draft.pending:
            raise ValueError("Tank is not awaiting an action")
        fallback = predicted_action(self.rules, state, tank_id, draft, memory)
        idle_costs = (
            {
                a: memory.idle_penalty(state, self.rules, a)
                for a in self.rules.actions(state, tank_id, draft)
            }
            if memory is not None and self.config.heuristic
            else {}
        )

        def check():
            if cancel_event is not None and cancel_event.is_set():
                raise TimeoutError
            if deadline is not None and perf_counter() >= deadline:
                raise TimeoutError
            stats.nodes += 1

        def choices(s, ids, d):
            options = []
            for i in ids:
                actions = self.rules.actions(s, i, d)
                priorities = action_priorities(s, i, self.rules, actions)
                if memory is not None and i == tank_id and s.turn == state.turn:
                    actions = memory.order_actions(s, self.rules, actions, priorities)
                else:
                    actions = sorted(actions, key=priorities.get)
                options.append(actions)
            for values in product(*options):
                yield dict(zip(ids, values))

        def max_value(s, d, remaining, alpha, beta, root_action=None):
            # Check terminal states before the depth limit.
            check()
            outcome = self.rules.outcome(s)
            if outcome is not None:
                return terminal_value(outcome, team), None
            if remaining == 0:
                return evaluate(s, team) - idle_costs.get(root_action, 0), None
            own = [tank_id] if tank_id in d.pending else []
            enemies = [i for i in d.pending if s.tank(i).team != team]
            # Nemesis applies only with >=3 live tanks; never hides other entities.
            if len(s.alive) >= 3 and nemesis in enemies:
                enemies = [nemesis]
            fixed = {
                i: predicted_action(self.rules, s, i, d)
                for i in d.pending
                if i not in own + enemies
            }
            value = float("-inf")
            best = None
            expanded = False
            for action_set in choices(s, own, d):
                if not expanded:
                    stats.expanded_nodes += 1
                    expanded = True
                selected = (
                    action_set.get(tank_id, root_action)
                    if s.turn == state.turn
                    else root_action
                )
                score = min_value(
                    s, d, remaining, alpha, beta, fixed | action_set, enemies, selected
                )
                if best is None or score > value:
                    value = score
                    best = action_set
                if self.config.alpha_beta:
                    if value >= beta:
                        stats.cutoffs += 1
                        return value, best
                    alpha = max(alpha, value)
            return value, best

        def min_value(s, d, remaining, alpha, beta, ours, enemies, root_action):
            # Prune replies that cannot improve the result.
            check()
            value = float("inf")
            expanded = False
            for action_set in choices(s, enemies, d):
                if not expanded:
                    stats.expanded_nodes += 1
                    expanded = True
                outcomes = self.rules.resolve(s, d, ours | action_set)
                expectation = 0
                for probability, next_draft in outcomes:
                    check()
                    stats.chance_outcomes += 1
                    # Chance outcomes need exact child values.
                    if next_draft.pending:
                        child, _ = max_value(
                            s,
                            next_draft,
                            remaining,
                            float("-inf"),
                            float("inf"),
                            root_action,
                        )
                    else:
                        next_s = self.rules.execute(s, next_draft)
                        outcome = self.rules.outcome(next_s)
                        if outcome is not None:
                            child = terminal_value(outcome, team)
                        else:
                            next_depth = None if remaining is None else remaining - 1
                            child, _ = max_value(
                                next_s,
                                self.rules.begin(next_s),
                                next_depth,
                                float("-inf"),
                                float("inf"),
                                root_action,
                            )
                    expectation += probability * child
                value = min(value, expectation)
                if self.config.alpha_beta:
                    if value <= alpha:
                        stats.cutoffs += 1
                        return value
                    beta = min(beta, value)
            return value

        result = SearchResult(fallback, evaluate(state, team), stats)
        # Pure minimax searches to terminal states.
        depths = (
            (
                range(1, self.config.depth + 1)
                if self.config.iterative_deepening
                else (self.config.depth,)
            )
            if self.config.heuristic
            else (None,)
        )
        for depth in depths:
            try:
                value, actions = max_value(
                    state, draft, depth, float("-inf"), float("inf")
                )
            except TimeoutError:
                stats.timed_out = True
                break
            if actions is None or tank_id not in actions:
                break
            result.action = actions[tank_id]
            result.score = value
            stats.completed_depth = depth or (state.max_turns - state.turn)
            stats.exact_terminal_search = depth is None
        stats.elapsed_seconds = perf_counter() - start
        return result


