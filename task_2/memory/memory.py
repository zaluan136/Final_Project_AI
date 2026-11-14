"""Short-term movement history, stored in RAM for one match."""

from collections import deque
from task_2.core.state import Direction, Action, Wall
from task_2.search.tactics import first_hit, bullet_cells


class MovementMemory:
    """Ten executed turns, not simulated nodes. No persistent disk storage.

    A changed HP/wall layout starts a new context. Nearby bullets suspend demotion
    because waiting, retreating or firing repeatedly can be tactically useful.
    """

    def __init__(self, tank_id):
        self.tank_id = tank_id
        self.history = deque(maxlen=10)
        self.context = None
        self.last_turn = -1
        self.idle_turns = 0

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
        previous = before.tank(self.tank_id)
        # Flying bullets and turning alone are not evidence of useful progress.
        self.idle_turns = (self.idle_turns+1 if
                           (tank.x, tank.y) == (previous.x, previous.y)
                           and self.signature(before) == context else 0)
        self.history.append((after.turn, tank.x, tank.y, tank.direction, action))
        self.last_turn = after.turn

    def visits(self, state, position):
        if self.danger_near(state) or self.signature(state) != self.context:
            return 0
        return sum(
            (x, y) == position
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

    def danger_near(self, state):
        tank = state.tank(self.tank_id)
        return any(abs(x-tank.x)+abs(y-tank.y) <= 1
                   for x, y in bullet_cells(state, self.tank_id))

    def productive_action(self, state, rules, action):
        tank = state.tank(self.tank_id)
        if rules.destination(state, self.tank_id, action) is not None:
            return True
        direction = tank.direction
        if action.name.startswith("MOVE_"):
            direction = Direction[action.value]
            if direction == tank.direction:
                return False
        elif action is not Action.FIRE:
            return False
        target = first_hit(state, tank.x, tank.y, direction)
        return target is not None and (
            isinstance(target, Wall) or getattr(target, "team", tank.team) != tank.team)

    def idle_penalty(self, state, rules, action):
        """Soft heuristic cost after four idle turns; never excludes an action.

        Keep productive shots/aiming, movement and nearby-bullet tactics intact.
        Terminal utility is handled before this cost in the search.
        """
        if (self.idle_turns < 4 or self.signature(state) != self.context
                or self.danger_near(state) or self.productive_action(state, rules, action)):
            return 0
        return min(48, 8*(self.idle_turns-3))

    def action_rank(self, state, rules, action):
        """Order only: no action is forbidden, and exact utilities stay intact."""
        if not action.name.startswith("MOVE_"):
            if self.productive_action(state, rules, action):
                return 0
            tank = state.tank(self.tank_id)
            return max(0, self.visits(state, (tank.x, tank.y))-2)
        tank = state.tank(self.tank_id)
        dest = rules.destination(state, self.tank_id, action)
        visits = self.visits(state, dest or (tank.x, tank.y))
        unchanged = dest is None and Direction[action.value] == tank.direction
        return max(0, visits - 1) + (2 if unchanged and visits >= 2 else 0)


