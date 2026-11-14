"""Short-term movement history, stored in RAM for one match."""

from collections import deque
from task_2.core.state import Direction


class MovementMemory:
    """Ten executed turns, not simulated nodes. No persistent disk storage.

    A changed HP/wall layout starts a new context. Bullets suspend demotion
    because waiting, retreating or firing repeatedly can be tactically useful.
    """

    def __init__(self, tank_id):
        self.tank_id = tank_id
        self.history = deque(maxlen=10)
        self.context = None
        self.last_turn = -1

    @staticmethod
    def signature(state):
        return (
            tuple((t.id, t.team, t.hp) for t in state.tanks),
            tuple((b.team, b.x, b.y, b.hp) for b in state.bases),
            tuple(sorted((w.x, w.y, w.hp) for w in state.walls)),
        )

    def observe(self, before, action, after):
        if after.turn <= self.last_turn:
            return
        context = self.signature(after)
        if context != self.context:
            self.history.clear()
            self.context = context
        tank = after.tank(self.tank_id)
        self.history.append((after.turn, tank.x, tank.y, tank.direction, action))
        self.last_turn = after.turn

    def visits(self, state, position):
        if state.bullets or self.signature(state) != self.context:
            return 0
        return sum(
            (x, y) == position and action.name.startswith("MOVE_")
            for _, x, y, _, action in self.history
        )

    def order_actions(self, state, rules, actions, tactical=None):
        """Stable priority queue: repeated moves go later, never disappear.

        Repetition adds to the tactical priority number (lower is better).
        For equal repetition counts, try the least recently visited target.
        Only exploration order and ties change; higher search values win.
        """
        tank = state.tank(self.tank_id)

        def priority(action):
            rank = self.action_rank(state, rules, action)
            level, distance = (tactical or {}).get(action, (0, 0))
            if rank == 0:
                return (level, 0, -1, distance)
            destination = rules.destination(state, self.tank_id, action) or (
                tank.x,
                tank.y,
            )
            recent = max(
                (
                    index
                    for index, (_, x, y, _, previous) in enumerate(self.history)
                    if (x, y) == destination and previous.name.startswith("MOVE_")
                ),
                default=-1,
            )
            return level + rank, rank, recent, distance

        return tuple(sorted(actions, key=priority))

    def action_rank(self, state, rules, action):
        """Order only: no action is forbidden, and exact utilities stay intact."""
        if not action.name.startswith("MOVE_"):
            return 0
        tank = state.tank(self.tank_id)
        dest = rules.destination(state, self.tank_id, action)
        visits = self.visits(state, dest or (tank.x, tank.y))
        unchanged = dest is None and Direction[action.value] == tank.direction
        return max(0, visits - 1) + (2 if unchanged and visits >= 2 else 0)
