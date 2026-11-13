from dataclasses import dataclass

Position = tuple[int, int]
DIGITS = frozenset(range(1, 10))


@dataclass(frozen=True)
class Cell:
    kind: str
    down: int | None = None
    across: int | None = None


@dataclass(frozen=True)
class Run:
    clue: Position
    direction: str
    total: int
    cells: tuple[Position, ...]

    @property
    def label(self):
        row, column = self.clue
        return f"R{row + 1}C{column + 1} {self.direction}={self.total}"


class Board:
    def __init__(self, name, grid):
        self.name = name
        self.grid = tuple(tuple(row) for row in grid)
        if not self.grid or not self.grid[0]:
            raise ValueError("Board must not be empty")
        self.height = len(self.grid)
        self.width = len(self.grid[0])
        if any(len(row) != self.width for row in self.grid):
            raise ValueError("Board must be rectangular")
        self.variables = tuple(
            (r, c)
            for r, row in enumerate(self.grid)
            for c, cell in enumerate(row)
            if cell.kind == "cell"
        )
        self.runs = []
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell.kind not in {"cell", "clue", "block"}:
                    raise ValueError("Unknown cell kind")
                for direction, total, dr, dc in (
                    ("across", cell.across, 0, 1),
                    ("down", cell.down, 1, 0),
                ):
                    if total is None:
                        continue
                    if cell.kind != "clue" or type(total) is not int:
                        raise ValueError("Invalid clue")
                    cells = []
                    nr, nc = r + dr, c + dc
                    while nr < self.height and nc < self.width:
                        if self.grid[nr][nc].kind != "cell":
                            break
                        cells.append((nr, nc))
                        nr, nc = nr + dr, nc + dc
                    if not 2 <= len(cells) <= 9:
                        raise ValueError("Each run needs 2 to 9 cells")
                    self.runs.append(Run((r, c), direction, total, tuple(cells)))
        self.runs = tuple(self.runs)
        self.cell_runs = {
            cell: tuple(run for run in self.runs if cell in run.cells)
            for cell in self.variables
        }
        if not self.variables or any(
            {run.direction for run in runs} != {"across", "down"} or len(runs) != 2
            for runs in self.cell_runs.values()
        ):
            raise ValueError("Each white cell needs one across and one down run")


class KakuroCSP:
    def __init__(self, board):
        self.board = board
        self.neighbors = {
            cell: set().union(*(set(run.cells) for run in board.cell_runs[cell]))
            - {cell}
            for cell in board.variables
        }

    def initial_domains(self):
        return {cell: set(DIGITS) for cell in self.board.variables}

    def run_possible(self, run, assignment, domains):
        values = [assignment[cell] for cell in run.cells if cell in assignment]
        if len(values) != len(set(values)):
            return False
        remaining = [cell for cell in run.cells if cell not in assignment]
        target = run.total - sum(values)
        if not remaining:
            return target == 0
        available = [domains[cell] - set(values) for cell in remaining]
        if any(not domain for domain in available):
            return False
        pool = sorted(set().union(*available))
        count = len(remaining)
        if len(pool) < count:
            return False
        lower = max(sum(min(domain) for domain in available), sum(pool[:count]))
        upper = min(sum(max(domain) for domain in available), sum(pool[-count:]))
        return lower <= target <= upper

    def consistent(self, cell, value, assignment, domains):
        if value not in domains[cell] or value not in DIGITS:
            return False
        trial = dict(assignment)
        trial[cell] = value
        return all(
            self.run_possible(run, trial, domains) for run in self.board.cell_runs[cell]
        )

    def is_solution(self, assignment):
        if set(assignment) != set(self.board.variables):
            return False
        if any(
            type(value) is not int or value not in DIGITS
            for value in assignment.values()
        ):
            return False
        return all(
            sum(assignment[cell] for cell in run.cells) == run.total
            and len({assignment[cell] for cell in run.cells}) == len(run.cells)
            for run in self.board.runs
        )
