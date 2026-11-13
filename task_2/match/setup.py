"""Terrain-only map and pre-match placement API; no automatic spawn."""

from dataclasses import replace
from pathlib import Path
from task_2.core.state import GameState, Tank, Base, Wall, Direction


def parse_map(text):
    rows = text.splitlines()
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Map must be a nonempty rectangle")
    if any(c not in ".#" for row in rows for c in row):
        raise ValueError("Map accepts only . and #")
    return GameState(
        len(rows[0]),
        len(rows),
        (),
        (),
        tuple(
            Wall(x, y)
            for y, row in enumerate(rows)
            for x, c in enumerate(row)
            if c == "#"
        ),
    )


def load_map(path):
    """Load terrain or preset: A/B = bases, a/b = tanks of each team."""
    text = Path(path).read_text(encoding="utf-8-sig")
    rows = text.splitlines()
    if any(c not in ".#ABab" for row in rows for c in row):
        raise ValueError("Map accepts . # A B a b only")
    terrain = parse_map(
        "\n".join("".join(c if c in ".#" else "." for c in row) for row in rows)
    )
    if not any(c in "ABab" for c in text):
        return terrain
    if text.count("A") != 1 or text.count("B") != 1:
        raise ValueError("Preset needs exactly one A base and one B base")
    setup = MatchSetup(terrain)
    for marker in "AB":
        x, y = next(
            (x, y)
            for y, row in enumerate(rows)
            for x, c in enumerate(row)
            if c == marker
        )
        setup.place_base(x, y)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in "ab":
                tid = setup.place_tank(
                    x, y, Direction.RIGHT if c == "a" else Direction.LEFT
                )
                setup.assign(tid, 0 if c == "a" else 1)
    return setup.start()


def export_map(state, name, directory=None, overwrite=False):
    """Save terrain in the same . / # format accepted by load_map."""
    name = name.strip()
    if name.lower().endswith(".txt"):
        name = name[:-4].strip()
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if (
        not name
        or name in {".", ".."}
        or any(c in name for c in '/\\<>:"|?*')
        or name.endswith(".")
        or name.upper() in reserved
    ):
        raise ValueError("Enter a valid map name without path or special characters")
    folder = (
        Path(directory)
        if directory is not None
        else Path(__file__).resolve().parents[1] / "maps"
    )
    folder.mkdir(parents=True, exist_ok=True)
    walls = {(wall.x, wall.y) for wall in state.walls if wall.hp > 0}
    content = (
        "\n".join(
            "".join("#" if (x, y) in walls else "." for x in range(state.width))
            for y in range(state.height)
        )
        + "\n"
    )
    path = folder / f"{name}.txt"
    try:
        with path.open("w" if overwrite else "x", encoding="utf-8") as output:
            output.write(content)
    except FileExistsError as error:
        raise ValueError(f"{path.name} already exists; choose another name") from error
    return path


class MatchSetup:
    def __init__(self, terrain):
        if terrain.tanks or terrain.bases or terrain.bullets:
            raise ValueError("Terrain only")
        self.state = terrain
        self.next_id = 0

    def place_base(self, x, y):
        team = next(
            (i for i in (0, 1) if i not in {b.team for b in self.state.bases}), None
        )
        if team is None:
            raise ValueError("Only two bases")
        self.state = replace(self.state, bases=self.state.bases + (Base(team, x, y),))
        return team

    def place_tank(self, x, y, direction=Direction.UP):
        tank = Tank(self.next_id, x, y, direction)
        self.state = replace(self.state, tanks=self.state.tanks + (tank,))
        self.next_id += 1
        return tank.id

    def assign(self, tid, team):
        self.state.tank(tid)
        if team not in {b.team for b in self.state.bases}:
            raise ValueError("Place base first")
        self.state = replace(
            self.state,
            tanks=tuple(
                replace(t, team=team) if t.id == tid else t for t in self.state.tanks
            ),
        )

    def remove_base(self, team):
        self.state = replace(
            self.state,
            bases=tuple(b for b in self.state.bases if b.team != team),
            tanks=tuple(
                replace(t, team=None) if t.team == team else t for t in self.state.tanks
            ),
        )

    def remove_tank(self, tid):
        self.state.tank(tid)
        self.state = replace(
            self.state, tanks=tuple(t for t in self.state.tanks if t.id != tid)
        )

    def start(self, max_turns=300):
        state = replace(self.state, max_turns=max_turns)
        state.validate_ready()
        return state
