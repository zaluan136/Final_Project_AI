"""Headless coordinator: shared AI budget, human input, pause, retries.
Calls are synchronous and bounded cooperatively for built-in agents. play.py
calls collect() in a worker; bot_loader.py isolates external bots in processes.
The shared match deadline remains a soft wall-clock budget.
"""

from dataclasses import dataclass
from random import Random
from time import perf_counter
from threading import Event
from task_2.core.state import Action
from task_2.core.rules import Draft, GameRules
from task_2.search.agents import SearchAgent
from task_2.search.algorithms import predicted_action


@dataclass(frozen=True)
class MatchConfig:
    ai_time_limit_enabled: bool = True
    ai_turn_budget_ms: int = 950

    def __post_init__(self):
        if type(self.ai_time_limit_enabled) is not bool:
            raise ValueError("Toggle must be bool")
        if type(self.ai_turn_budget_ms) is not int or self.ai_turn_budget_ms <= 0:
            raise ValueError("Budget must be a positive integer in ms")


class MatchRunner:
    def __init__(
        self, state, agents=None, config=None, seed=None, player_priority_enabled=True
    ):
        state.validate_ready()
        self.state = state
        self.rules = GameRules()
        self.config = config or MatchConfig()
        self.next_config = self.config
        self.agents = agents or {
            t.id: SearchAgent(self.rules, t.id, seed=t.id) for t in state.tanks
        }
        if set(self.agents) != {t.id for t in state.tanks}:
            raise ValueError("Provide an agent for every tank")
        self.rng = Random(seed)
        self.human = None
        self.player_priority_enabled = player_priority_enabled
        self.set_player_priority(player_priority_enabled)
        # Search must simulate the same contest rule as the live match.
        for agent in self.agents.values():
            if isinstance(agent, SearchAgent):
                agent.searcher.rules = self.rules
        self.paused = False
        self.draft = self.rules.begin(state)
        self.proposals = {}
        self.ai_spent_ms = 0.0
        self.last_ai_spent_ms = 0.0
        self.fallback_ids = set()
        self.cancel_event = Event()
        self.last_actions = {}
        self.events = []
        self.last_fallback_ids = set()

    @property
    def ready(self):
        return not self.draft.pending

    def configure(self, config):
        self.next_config = config  # takes effect at the next turn boundary

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def control(self, tank_id=None):
        if tank_id is not None and tank_id not in {t.id for t in self.state.alive}:
            raise ValueError("Control a living tank")
        self.human = tank_id
        self.rules.priority_tank = tank_id if self.player_priority_enabled else None
        self.paused = True
        if tank_id in self.draft.pending:
            self.proposals.pop(tank_id, None)
        # Already accepted action is locked; new ownership applies next turn.

    def set_player_priority(self, enabled):
        if type(enabled) is not bool:
            raise ValueError("Player priority toggle must be bool")
        self.player_priority_enabled = enabled
        self.rules.priority_tank = self.human if enabled else None

    def human_options(self):
        if self.human is None or self.human not in self.draft.pending:
            return ()
        return self.rules.actions(self.state, self.human, self.draft)

    def submit(self, action):
        if action not in self.human_options():
            raise ValueError("No pending human action or illegal action")
        self.proposals[self.human] = action

    def _observation(self):
        # Do not expose accepted FIRE/STAY/blocked-turn intent to retry agents.
        # Reserved movements are revealed by conflict resolution. Unknown
        # accepted nonmoves are approximated as STAY in their search model.
        accepted = tuple(
            (
                tid,
                (
                    a
                    if self.rules.destination(self.state, tid, a) is not None
                    else Action.STAY
                ),
            )
            for tid, a in self.draft.accepted
        )
        return Draft(accepted, self.draft.reserved, self.draft.pending)

    def collect(self):
        """Collect/resolve; stop for human retry or return ready. Never executes."""
        if self.paused or self.rules.outcome(self.state) is not None:
            return
        while self.draft.pending:
            if self.cancel_event.is_set():
                return
            start = perf_counter()
            observation = self._observation()
            ids = [
                i
                for i in self.draft.pending
                if i != self.human and i not in self.proposals
            ]
            # Rotate allocation order, not movement rights. Fairness of cell
            # lotteries is independent of this scheduling choice.
            if ids:
                offset = self.state.turn % len(ids)
                ids = ids[offset:] + ids[:offset]
            for index, tid in enumerate(ids):
                if self.cancel_event.is_set():
                    self.ai_spent_ms += (perf_counter() - start) * 1000
                    return
                elapsed = (perf_counter() - start) * 1000
                remaining = max(
                    0, self.config.ai_turn_budget_ms - self.ai_spent_ms - elapsed
                )
                fallback = predicted_action(
                    self.rules,
                    self.state,
                    tid,
                    observation,
                    getattr(self.agents[tid], "memory", None),
                )
                if self.config.ai_time_limit_enabled and remaining <= 1:
                    action = fallback
                    self.fallback_ids.add(tid)
                else:
                    # Keep 30% of remaining budget for retries/coordination.
                    deadline = (
                        perf_counter() + remaining * 0.7 / (len(ids) - index) / 1000
                        if self.config.ai_time_limit_enabled
                        else None
                    )
                    agent = self.agents[tid]
                    agent.cancel_event = self.cancel_event
                    try:
                        action = agent.choose_action(self.state, observation, deadline)
                    except Exception as error:
                        action = fallback
                        self.fallback_ids.add(tid)
                        self.events.append(
                            f"Tank {tid}: {type(error).__name__}; fallback"
                        )
                    if self.cancel_event.is_set():
                        self.ai_spent_ms += (perf_counter() - start) * 1000
                        return
                    result = getattr(agent, "last_result", None)
                    if result is not None and result.stats.completed_depth == 0:
                        self.fallback_ids.add(tid)
                    if action not in self.rules.actions(self.state, tid, self.draft):
                        action = fallback
                        self.fallback_ids.add(tid)
                        self.events.append(f"Tank {tid}: invalid action; fallback")
                self.proposals[tid] = action
            self.ai_spent_ms += (perf_counter() - start) * 1000
            if set(self.proposals) != set(self.draft.pending):
                return  # waiting for human, no clock runs
            start = perf_counter()
            self.draft = self.rules.sample(
                self.rules.resolve(self.state, self.draft, self.proposals), self.rng
            )
            if self.draft.pending:
                self.events.append(
                    "Retry: " + ", ".join(str(i) for i in self.draft.pending)
                )
            self.proposals = {}
            self.ai_spent_ms += (perf_counter() - start) * 1000
            if self.human in self.draft.pending:
                return  # ask for another action, no lost turn

    def commit(self):
        if self.paused or not self.ready:
            raise ValueError("Resume and finish choosing actions first")
        self.last_actions = dict(self.draft.accepted)
        before = self.state
        self.state = self.rules.execute(self.state, self.draft)
        for tid, action in self.last_actions.items():
            # Only the built-in agent has this memory contract. Never invoke
            # arbitrary external hooks from the UI/physics thread.
            if isinstance(self.agents[tid], SearchAgent):
                self.agents[tid].observe_turn(before, action, self.state)
        self.last_ai_spent_ms = self.ai_spent_ms
        self.ai_spent_ms = 0
        self.last_fallback_ids = set(self.fallback_ids)
        self.fallback_ids.clear()
        self.config = self.next_config
        self.proposals = {}
        if self.rules.outcome(self.state) is None:
            self.draft = self.rules.begin(self.state)
        return self.state
