"""Small tactical helpers: UCS routes and soft action priorities.

Route costs approximate turns (move=1, wall=HP+2 for shots/turning/move).
They guide adversarial search, never replace the game's collision rules.
"""
from functools import lru_cache
from heapq import heappop, heappush
from task_2.core.state import Action, Direction, Wall


def first_hit(state, x, y, direction):
    occupied = {(e.x, e.y): e for e in (*state.alive, *state.bases, *state.walls) if e.hp > 0}
    dx, dy = direction.value
    while state.inside(x+dx, y+dy):
        x, y = x+dx, y+dy
        if (x, y) in occupied:
            return occupied[x, y]
    return None


def base_threats(state, team):
    base = next(b for b in state.bases if b.team == team)
    enemies = [t for t in state.alive if t.team != team]
    threats = [t for t in enemies
               if first_hit(state, t.x, t.y, t.direction) == base
               or (base.hp <= 3 and abs(t.x-base.x)+abs(t.y-base.y) <= 4)]
    incoming = any(first_hit(state, b.x, b.y, b.direction) == base for b in state.bullets)
    return tuple(threats), incoming


@lru_cache(maxsize=256)
def route(state, tank_id):
    """UCS to a clear firing cell within three cells of the chosen target.

    Normally attack the enemy base; defend against a base threat instead.
    All other tanks/bases are blocked. Destructible walls have weighted cost.
    Return (cost, path), including the start. Empty path means unreachable.
    """
    tank = state.tank(tank_id)
    threats, _ = base_threats(state, tank.team)
    target = min(threats, key=lambda t: abs(t.x-tank.x)+abs(t.y-tank.y)) if threats else next(b for b in state.bases if b.team != tank.team)
    blocked = {(e.x, e.y) for e in (*state.alive, *state.bases) if e.hp > 0 and e != tank}
    walls = {(w.x, w.y): w.hp for w in state.walls if w.hp > 0}
    danger = bullet_cells(state, tank_id)
    enemies = [t for t in state.alive if t.team != tank.team]
    goals = set()
    for direction in Direction:
        dx, dy = direction.value
        for distance in range(1, 4):
            cell = target.x+dx*distance, target.y+dy*distance
            if not state.inside(*cell) or cell in blocked:
                break
            goals.add(cell)
            if cell in walls:
                break  # This firing cell becomes usable once its wall is destroyed.
    start = tank.x, tank.y
    queue = [(0, start)]
    costs, parents = {start: 0}, {}
    while queue:
        cost, cell = heappop(queue)
        if cost != costs[cell]:
            continue
        if cell in goals:
            path = [cell]
            while cell != start:
                cell = parents[cell]
                path.append(cell)
            return cost, tuple(reversed(path))
        for direction in Direction:
            dx, dy = direction.value
            nxt = cell[0]+dx, cell[1]+dy
            if not state.inside(*nxt) or nxt in blocked:
                continue
            candidate = cost + (walls[nxt]+2 if nxt in walls else 1)
            # Soft risk costs let UCS prefer a safer detour; cells stay reachable.
            if nxt in danger:
                candidate += 6
            if any(abs(nxt[0]-e.x)+abs(nxt[1]-e.y) <= 2 for e in enemies):
                candidate += 3
            if candidate < costs.get(nxt, float('inf')):
                costs[nxt], parents[nxt] = candidate, cell
                heappush(queue, (candidate, nxt))
    return state.width*state.height*6, ()


def bullet_cells(state, tank_id):
    """Existing bullets' next three cells, respecting current obstacles.

    Remove the focal tank when tracing, since it may move out of the way.
    This is a warning estimate; execute() remains authoritative.
    """
    blocked = {(e.x, e.y) for e in (*state.alive, *state.bases, *state.walls)
               if e.hp > 0 and e != state.tank(tank_id)}
    danger = set()
    for bullet in state.bullets:
        x, y = bullet.x, bullet.y
        danger.add((x, y))
        dx, dy = bullet.direction.value
        for _ in range(3):
            x, y = x+dx, y+dy
            if not state.inside(x, y):
                break
            danger.add((x, y))
            if (x, y) in blocked:
                break
    return danger


def action_priorities(state, tank_id, rules, actions):
    """Lower numbers are tried first; no legal action is removed."""
    tank = state.tank(tank_id)
    here = tank.x, tank.y
    _, path = route(state, tank_id)
    step = path[1] if len(path) > 1 else None
    hit = first_hit(state, tank.x, tank.y, tank.direction)
    enemies = [t for t in state.alive if t.team != tank.team]
    danger = bullet_cells(state, tank_id)
    threats, incoming = base_threats(state, tank.team)
    close = any(abs(t.x-tank.x)+abs(t.y-tank.y) <= 2 for t in enemies)
    urgent = bool(threats or incoming or close or here in danger)
    useful_wall = isinstance(hit, Wall) and (hit.x, hit.y) == step
    keys = {}
    for action in actions:
        dest = rules.destination(state, tank_id, action)
        position = dest or here
        if action is Action.FIRE and hit is not None and getattr(hit, 'team', tank.team) != tank.team:
            level = 0  # Engage an enemy, including an immediate winning shot.
        elif dest is not None and here in danger and dest not in danger:
            level = 1  # Escape existing bullets.
        elif dest is not None:
            level = 2 if (urgent or dest == step) and dest not in danger else 4
            if dest in danger:
                level = 7
        elif action is Action.FIRE and useful_wall:
            level = 6 if urgent else 3
        elif action.name.startswith('MOVE_') and Direction[action.value] != tank.direction and step is not None and (tank.x+Direction[action.value].value[0], tank.y+Direction[action.value].value[1]) == step:
            level = 6 if urgent else 3  # Turn towards a wall before firing.
        elif action is Action.STAY:
            level = 5
        else:
            level = 6
        distance = abs(position[0]-step[0])+abs(position[1]-step[1]) if step else 0
        if close and not threats and not incoming:
            distance = -min(abs(position[0]-e.x)+abs(position[1]-e.y) for e in enemies)
        keys[action] = (level, distance)
    return keys
