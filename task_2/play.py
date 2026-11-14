"""Pygame playground. Run: python -m task_2.

The engine stays independent of pygame.
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event
from time import perf_counter

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "task_2"

import pygame

from task_2.search.agents import CONFIGURATIONS, SearchAgent
from .benchmark import compare
from task_2.match.bot_loader import FileAgent
from task_2.match.runner import MatchConfig, MatchRunner
from task_2.core.rules import GameRules
from task_2.match.setup import MatchSetup, export_map, load_map, parse_map
from task_2.core.state import Action, Direction, Wall

COLORS = [(74, 169, 255), (255, 112, 105)]
BG, PANEL, FG, MUTED = (20, 25, 34), (30, 38, 50), (229, 235, 244), (157, 171, 190)
CANVAS_SIZE = (1200, 820)
MODE_LABELS = ["Minimax", "Alpha-Beta", "Heuristic Minimax", "Heuristic + AB"]
MODES = list(CONFIGURATIONS)
KEY_ACTION = {
    pygame.K_w: Action.MOVE_UP,
    pygame.K_UP: Action.MOVE_UP,
    pygame.K_s: Action.MOVE_DOWN,
    pygame.K_DOWN: Action.MOVE_DOWN,
    pygame.K_a: Action.MOVE_LEFT,
    pygame.K_LEFT: Action.MOVE_LEFT,
    pygame.K_d: Action.MOVE_RIGHT,
    pygame.K_RIGHT: Action.MOVE_RIGHT,
    pygame.K_SPACE: Action.FIRE,
    pygame.K_x: Action.STAY,
}


class Playground:
    def __init__(self, screen=None):
        self.screen = (
            screen if screen is not None else pygame.display.set_mode(CANVAS_SIZE)
        )
        self.embedded_mouse_pos: tuple[int, int] | None = None
        pygame.display.set_caption("Tank Battle | temporary playground")
        self.set_fonts()
        self.clock = pygame.time.Clock()
        self.asset_dir = Path(__file__).resolve().parent / "asset"
        self.sprites = {
            path.stem: pygame.image.load(str(path)).convert_alpha()
            for path in self.asset_dir.glob("*.png")
        }
        self.scaled_sprites = {}
        self.fire_effects = []
        self.bullet_fades = []
        self.panel_open = True
        self.match_initial_state = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.job = None
        self.after_job = None
        self.cancel_benchmark = Event()
        self.running = True
        self.runner = None
        self.setup = MatchSetup(parse_map("\n".join(["." * 13] * 11)))
        self.selected = None
        self.tool = "select"
        self.mode_by_id = {}
        self.nemesis = True
        self.limit = True
        self.player_priority = True
        self.fields = {
            "turns": "300",
            "budget": "950",
            "depth": "2",
            "delay": "400",
            "path": "",
            "map_name": "",
        }
        self.active_field = None
        self.select_all_text = False
        self.field_rects = {}
        self.buttons = []
        self.message = "Place two bases and 2-4 tanks. Select a tank, then assign A/B."
        self.last_step = 0
        self.single_step = False
        self.overlay = False
        self.bench_suite = "terminal"
        self.bench_rows = []
        self.geometry()

    def set_fonts(self, scale=None):
        def make_font(size, bold):
            if scale is None:
                return pygame.font.SysFont("segoeui", size, bold=bold)
            from .scaled_canvas import ScaledFont
            return ScaledFont(size, bold, scale)
        self.font = make_font(18, False)
        self.small = make_font(15, False)
        self.action_font = make_font(16, True)
        self.title = make_font(25, True)
        self.turn_font = make_font(28, True)
        self.result_font = make_font(36, True)

    def resize_canvas(self, size):
        from .scaled_canvas import ScaledCanvas

        self.screen = ScaledCanvas(size)
        scale = min(size[0] / CANVAS_SIZE[0], size[1] / CANVAS_SIZE[1])
        self.set_fonts(scale)

    @staticmethod
    def draw_rect(target, *args, **kwargs):
        if hasattr(target, "draw_rect"):
            return target.draw_rect(*args, **kwargs)
        return pygame.draw.rect(target, *args, **kwargs)

    @staticmethod
    def draw_circle(target, *args, **kwargs):
        if hasattr(target, "draw_circle"):
            return target.draw_circle(*args, **kwargs)
        return pygame.draw.circle(target, *args, **kwargs)

    def geometry(self):
        state = self.state
        width = 690 if self.panel_open else self.screen.get_width() - 40
        top = 120 if self.runner else 75
        height = (550 if self.panel_open else 650) if self.runner else (610 if self.panel_open else self.screen.get_height() - 130)
        limit = 52 if self.panel_open else max(width, height)
        self.cell = max(1, min(limit, width // state.width, height // state.height))
        self.board = pygame.Rect(
            0, 0, self.cell * state.width, self.cell * state.height
        )
        self.board.center = (20 + width // 2, top + height // 2)

    @property
    def state(self):
        return self.runner.state if self.runner else self.setup.state

    def number(self, name):
        value = int(self.fields[name])
        if value < (0 if name == "delay" else 1):
            raise ValueError(f"{name} is invalid")
        return value

    def notify(self, action):
        try:
            action()
        except Exception as error:
            self.message = str(error)

    def text(self, text, x, y, color=FG, small=False):
        surface = (self.small if small else self.font).render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def button(self, label, rect, callback, active=False, style="neutral"):
        rect = pygame.Rect(rect)
        palettes = {
            "neutral": ((56, 69, 87), (39, 49, 65), (85, 102, 125)),
            "primary": ((36, 143, 100), (22, 100, 73), (92, 218, 164)),
            "info": ((46, 112, 183), (29, 76, 132), (108, 178, 245)),
            "warning": ((156, 101, 35), (110, 66, 24), (243, 184, 93)),
            "danger": ((158, 65, 71), (113, 40, 48), (232, 125, 133)),
            "violet": ((113, 86, 169), (76, 55, 126), (183, 153, 237)),
        }
        top, bottom, border = palettes[
            "info" if active and style == "neutral" else style
        ]
        mouse_pos = self.embedded_mouse_pos
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            ratio = y / max(1, rect.height - 1)
            color = tuple(
                min(255, round(a + (b - a) * ratio) + (14 if hovered else 0))
                for a, b in zip(top, bottom)
            )
            pygame.draw.line(surface, color, (0, y), (rect.width - 1, y))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.draw_rect(mask, (255, 255, 255), mask.get_rect(), border_radius=6)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(surface, rect)
        self.draw_rect(
            self.screen, border, rect, 2 if active or hovered else 1, border_radius=6
        )
        font = self.action_font if style != "neutral" else self.small
        text = font.render(str(label), True, (250, 252, 255))
        position = (
            text.get_rect(center=rect.center)
            if style != "neutral"
            else text.get_rect(midleft=(rect.x + 9, rect.centery))
        )
        self.screen.blit(text, position)
        self.buttons.append((rect, callback))

    def field(self, name, label, rect):
        rect = pygame.Rect(rect)
        self.text(label, rect.x, rect.y - 20, MUTED, True)
        self.draw_rect(self.screen, (15, 21, 30), rect, border_radius=4)
        if name == self.active_field:
            self.draw_rect(self.screen, COLORS[0], rect, 1, border_radius=4)
        visible = self.fields[name]
        while self.small.size(visible)[0] > rect.width - 14:
            visible = visible[1:]
        self.text(visible, rect.x + 6, rect.y + 6, small=True)
        self.field_rects[name] = rect

    def defer(self, action):
        """Pause/handoff at worker boundary; never mutate a busy runner."""
        if self.future is not None:
            self.after_job = action
            if self.runner:
                self.runner.cancel_event.set()
            self.cancel_benchmark.set()
            self.message = "Stopping computation..."
        else:
            self.notify(action)

    def start(self):
        state = self.setup.start(self.number("turns"))
        self.match_initial_state = state
        self.new_match(state)

    def new_match(self, state):
        self.fire_effects.clear()
        self.bullet_fades.clear()
        rules = GameRules()
        agents = {}
        for tank in state.tanks:
            choice = self.mode_by_id.get(tank.id, "heuristic_alpha_beta")
            if choice.startswith("file:"):
                agents[tank.id] = FileAgent(choice[5:], tank.id)
            else:
                agents[tank.id] = SearchAgent(
                    rules,
                    tank.id,
                    choice,
                    self.number("depth"),
                    seed=tank.id,
                    use_nemesis=self.nemesis,
                )
        # Gameplay gets a fresh lottery each match; tests can still seed the runner.
        self.runner = MatchRunner(
            state,
            agents,
            MatchConfig(self.limit, self.number("budget")),
            player_priority_enabled=self.player_priority,
        )
        self.runner.resume()
        self.message = "Match started. Select a tank and Take control to play."
        self.single_step = False
        self.geometry()

    def reset_match(self):
        if self.match_initial_state is None:
            raise ValueError("Start a match first")
        self.new_match(self.match_initial_state)
        self.message = "Match restarted at turn 0."

    def toggle_panel(self):
        self.panel_open = not self.panel_open
        self.active_field = None
        if not self.panel_open:
            self.tool = "select"
        self.geometry()

    def reset(self):
        self.runner = None
        self.match_initial_state = None
        self.fire_effects.clear()
        self.bullet_fades.clear()
        self.selected = None
        self.overlay = False
        self.single_step = False
        self.message = "Back to setup; original placements restored."
        self.geometry()

    def pause_resume(self):
        if self.runner:
            if self.runner.paused:
                self.runner.cancel_event.clear()
                self.runner.resume()
                self.message = (
                    "Running. P pauses; click a tank and Take control to play."
                )
            else:
                self.runner.pause()
                self.message = "Paused."

    def step(self):
        if self.runner:
            self.runner.cancel_event.clear()
            self.runner.resume()
            self.single_step = True

    def control(self, tank_id):
        if self.runner is None:
            raise ValueError("Start a match first")
        self.runner.control(tank_id)
        self.runner.cancel_event.clear()
        self.runner.resume()
        self.single_step = False
        self.message = (
            "AI controls all tanks."
            if tank_id is None
            else f"Control T{tank_id}. WASD/arrows, Space=fire, X=stay."
        )

    def take_control(self):
        if self.selected is None:
            raise ValueError("Select a living tank first")
        self.control(self.selected)

    def set_tool(self, tool):
        self.tool = tool

    def assign(self, team):
        if self.selected is None:
            raise ValueError("Select a tank first")
        self.setup.assign(self.selected, team)

    def rotate(self):
        if self.selected is None:
            raise ValueError("Select a tank first")
        directions = list(Direction)
        tank = self.setup.state.tank(self.selected)
        direction = directions[(directions.index(tank.direction) + 1) % 4]
        self.setup.state = replace(
            self.setup.state,
            tanks=tuple(
                replace(t, direction=direction) if t.id == tank.id else t
                for t in self.setup.state.tanks
            ),
        )

    def cycle_mode(self):
        if self.selected is None:
            raise ValueError("Select a tank first")
        current = self.mode_by_id.get(self.selected, MODES[-1])
        self.mode_by_id[self.selected] = (
            MODES[(MODES.index(current) + 1) % 4] if current in MODES else MODES[0]
        )

    def load_bot(self):
        if self.selected is None:
            raise ValueError("Select a tank first")
        chosen = self.choose_file(bot=True)
        if not chosen:
            return
        path = Path(chosen).resolve(strict=True)
        if path.suffix != ".py":
            raise ValueError("Choose a .py bot file")
        self.mode_by_id[self.selected] = "file:" + str(path)
        self.message = f"T{self.selected}: external bot {path.name}"

    def choose_file(self, save=False, bot=False):
        """Native picker on the UI thread; cancelling leaves the setup intact."""
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
            folder = Path(__file__).resolve().parent
            maps = folder / "maps"
            initialdir = str(folder if bot or not maps.is_dir() else maps)
            filetypes = [("Python bot", "*.py")] if bot else [("Text map", "*.txt")]
            if save:
                return filedialog.asksaveasfilename(
                    title="Export terrain map",
                    defaultextension=".txt",
                    confirmoverwrite=True,
                    initialfile="my_map.txt",
                    parent=root,
                    initialdir=initialdir,
                    filetypes=filetypes,
                )
            return filedialog.askopenfilename(
                title="Choose bot" if bot else "Choose map",
                parent=root,
                initialdir=initialdir,
                filetypes=filetypes,
            )
        finally:
            root.destroy()
            # Discard clicks/keys generated while the native dialog was open.
            pygame.event.clear(
                (
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                    pygame.KEYDOWN,
                    pygame.KEYUP,
                )
            )

    def load_terrain(self):
        chosen = self.choose_file()
        if not chosen:
            return
        state = load_map(chosen)
        self.setup = MatchSetup(replace(state, tanks=(), bases=()))
        self.setup.state = state
        self.setup.next_id = max((t.id for t in state.tanks), default=-1) + 1
        self.selected = None
        self.mode_by_id.clear()
        self.geometry()
        self.message = (
            "Preset loaded; ready to START or edit placements."
            if state.tanks
            else "Map loaded; place bases and tanks yourself."
        )

    def export_terrain(self):
        chosen = self.choose_file(save=True)
        if not chosen:
            return
        target = Path(chosen)
        path = export_map(self.setup.state, target.name, target.parent, overwrite=True)
        self.message = f"Terrain map saved to {path}"

    def apply_budget(self):
        if self.runner is None:
            raise ValueError("Start a match first")
        self.runner.configure(MatchConfig(self.limit, self.number("budget")))
        self.message = "Budget changes apply next turn."

    def board_click(self, position, right=False):
        x, y = (position[0] - self.board.x) // self.cell, (
            position[1] - self.board.y
        ) // self.cell
        tank = next((t for t in self.state.alive if (t.x, t.y) == (x, y)), None)
        if self.runner or not self.panel_open or self.tool == "select" or right:
            self.selected = tank.id if tank else None
            return
        if self.tool == "base":
            self.setup.place_base(x, y)
        elif self.tool == "tank":
            self.selected = self.setup.place_tank(x, y)
        elif self.tool == "wall":
            self.setup.state = replace(
                self.setup.state, walls=self.setup.state.walls + (Wall(x, y),)
            )
        elif self.tool == "erase":
            if tank:
                self.setup.remove_tank(tank.id)
                if self.selected == tank.id:
                    self.selected = None
            base = next(
                (b for b in self.setup.state.bases if (b.x, b.y) == (x, y)), None
            )
            if base:
                self.setup.remove_base(base.team)
            self.setup.state = replace(
                self.setup.state,
                walls=tuple(w for w in self.setup.state.walls if (w.x, w.y) != (x, y)),
            )

    def benchmark(self):
        if self.runner:
            self.runner.pause()
        state = self.state
        state.validate_ready()
        if GameRules().outcome(state) is not None:
            raise ValueError("Benchmark from an unfinished game or setup")
        self.cancel_benchmark.clear()
        self.future = self.executor.submit(
            compare,
            state,
            min(950, self.number("budget")),
            self.number("depth"),
            3,
            self.cancel_benchmark,
        )
        self.job = "benchmark"
        self.message = "Comparing four algorithms on identical snapshots..."

    def poll_worker(self):
        if self.future is None or not self.future.done():
            return
        try:
            result = self.future.result()
            if self.job == "benchmark" and result is not None:
                self.bench_rows = result
                self.overlay = True
                self.message = "Terminal suite = final-turn scenarios; Budget suite = current snapshot."
            elif self.runner and self.runner.events:
                self.message = self.runner.events[-1]
                self.runner.events = self.runner.events[-8:]
        except Exception as error:
            self.message = f"{type(error).__name__}: {error}"
            if self.runner:
                self.runner.pause()
        self.future = None
        self.job = None
        if self.after_job:
            action, self.after_job = self.after_job, None
            self.notify(action)

    def tick_match(self):
        if not self.runner or self.future is not None or self.overlay:
            return
        runner = self.runner
        outcome = runner.rules.outcome(runner.state)
        if outcome is not None:
            result = (
                "DRAW"
                if outcome.winner is None
                else f'Team {"AB"[outcome.winner]} wins'
            )
            self.message = f"{result}: {outcome.reason}"
            return
        if runner.paused:
            return
        if runner.ready:
            if (perf_counter() - self.last_step) * 1000 < self.number("delay"):
                return
            before = runner.state
            firing = [
                (t.x, t.y, t.direction)
                for t in runner.state.alive
                if dict(runner.draft.accepted).get(t.id) is Action.FIRE
            ]
            runner.commit()
            now = pygame.time.get_ticks()
            self.fire_effects = [(x, y, direction, now) for x, y, direction in firing]
            # Bullets advance up to three cells in execute(). Mark the end of
            # that travel, including shots absorbed by an entity or the edge.
            occupied = {
                (e.x, e.y)
                for e in (*before.tanks, *before.bases, *before.walls)
                if e.hp > 0
            }
            fades = []
            for x, y, direction in [
                *((b.x, b.y, b.direction) for b in before.bullets),
                *firing,
            ]:
                start_x, start_y = x, y
                dx, dy = direction.value
                for _ in range(3):
                    nx, ny = x + dx, y + dy
                    if not before.inside(nx, ny):
                        break
                    x, y = nx, ny
                    if (x, y) in occupied:
                        break
                if (x, y) != (start_x, start_y):
                    fades.append((start_x, start_y, x, y, direction, now))
            self.bullet_fades = fades
            self.last_step = perf_counter()
            if self.single_step:
                runner.pause()
                self.single_step = False
            return
        waiting = (
            runner.human in runner.draft.pending
            and runner.human not in runner.proposals
        )
        other_pending = any(
            i != runner.human and i not in runner.proposals
            for i in runner.draft.pending
        )
        if waiting and not other_pending:
            self.message = (
                f"T{runner.human}: choose an action (or retry). Space=fire, X=stay."
            )
            return
        runner.cancel_event.clear()
        self.future = self.executor.submit(runner.collect)
        self.job = "collect"

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            if self.runner:
                self.runner.cancel_event.set()
            self.cancel_benchmark.set()
            return
        if self.runner and self.runner.rules.outcome(self.state) is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, callback in reversed(self.buttons):
                    if rect.collidepoint(event.pos):
                        self.notify(callback)
                        break
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            for name, rect in self.field_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_field = name
                    self.select_all_text = True
                    return
            self.active_field = None
            for rect, callback in reversed(self.buttons):
                if event.button == 1 and rect.collidepoint(event.pos):
                    self.notify(callback)
                    return
            if not self.overlay and self.board.collidepoint(event.pos):
                self.notify(lambda: self.board_click(event.pos, event.button == 3))
        if event.type == pygame.KEYDOWN:
            if self.active_field:
                if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_a:
                    self.select_all_text = True
                    return
                if (
                    event.mod & pygame.KMOD_CTRL
                    and event.key == pygame.K_v
                    and self.active_field == "path"
                ):
                    pygame.scrap.init()
                    raw = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if raw:
                        pasted = (
                            raw.decode("utf-8", errors="ignore")
                            .replace("\x00", "")
                            .strip()
                        )
                        self.fields["path"] = (
                            "" if self.select_all_text else self.fields["path"]
                        ) + pasted
                        self.select_all_text = False
                    return
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    self.fields[self.active_field] = (
                        ""
                        if self.select_all_text
                        else self.fields[self.active_field][:-1]
                    )
                    self.select_all_text = False
                elif event.unicode.isprintable():
                    if (
                        self.active_field in ("path", "map_name")
                        or event.unicode.isdecimal()
                    ):
                        if self.select_all_text:
                            self.fields[self.active_field] = ""
                        self.fields[self.active_field] += event.unicode
                        self.select_all_text = False
                return
            if event.key == pygame.K_ESCAPE:
                if self.overlay:
                    self.overlay = False
                elif self.runner:
                    self.defer(self.runner.pause)
            elif event.key == pygame.K_p:
                self.defer(self.pause_resume)
            elif self.runner and event.key in KEY_ACTION:
                action = KEY_ACTION[event.key]
                runner = self.runner
                self.defer(lambda: runner.submit(action))

    def sprite(self, name, size, direction=Direction.UP):
        key = (name, size, direction)
        if key not in self.scaled_sprites:
            image = self.sprites[name]
            angle = {
                Direction.UP: 0,
                Direction.RIGHT: -90,
                Direction.DOWN: 180,
                Direction.LEFT: 90,
            }[direction]
            if angle:
                image = pygame.transform.rotate(image, angle)
            self.scaled_sprites[key] = pygame.transform.scale(image, (size, size))
        return self.scaled_sprites[key]

    def draw_board(self):
        s = self.state
        for y in range(s.height):
            for x in range(s.width):
                rect = pygame.Rect(
                    self.board.x + x * self.cell,
                    self.board.y + y * self.cell,
                    self.cell,
                    self.cell,
                )
                self.screen.blit(self.sprite("ground", self.cell), rect)
                self.draw_rect(self.screen, (38, 51, 43), rect, 1)

        def box(entity, inset=6):
            return pygame.Rect(
                self.board.x + entity.x * self.cell + inset,
                self.board.y + entity.y * self.cell + inset,
                max(1, self.cell - 2 * inset),
                max(1, self.cell - 2 * inset),
            )

        for wall in s.walls:
            rect = box(wall, 0)
            self.screen.blit(self.sprite("wall", self.cell), rect)
            self.text(wall.hp, rect.x + 3, rect.y + 2, FG, True)
        for base in s.bases:
            if base.hp <= 0:
                continue
            rect = box(base, 0)
            self.screen.blit(self.sprite(f'base_{"ab"[base.team]}', self.cell), rect)
            self.draw_rect(self.screen, (20, 26, 30), (rect.x + 2, rect.y + 2, 29, 17))
            self.text(f'{"AB"[base.team]}:{base.hp}', rect.x + 3, rect.y + 2, FG, True)
        for tank in s.tanks:
            if tank.hp <= 0:
                continue
            rect = box(tank, 0)
            name = "tank_neutral" if tank.team is None else f'tank_{"ab"[tank.team]}'
            self.screen.blit(self.sprite(name, self.cell, tank.direction), rect)
            center = rect.center
            if tank.id == self.selected:
                self.draw_rect(self.screen, FG, rect.inflate(8, 8), 2, border_radius=5)
            if self.runner and tank.id == self.runner.human:
                self.draw_circle(
                    self.screen, (255, 220, 95), center, self.cell // 2 - 2, 2
                )
            label = f'{"?" if tank.team is None else "AB"[tank.team]}{tank.id}'
            self.draw_rect(self.screen, (20, 26, 30), (rect.x + 2, rect.y + 2, 26, 17))
            self.text(label, rect.x + 3, rect.y + 2, FG, True)
            self.draw_rect(
                self.screen, (20, 26, 30), (rect.right - 16, rect.bottom - 18, 14, 16)
            )
            self.text(tank.hp, rect.right - 15, rect.bottom - 19, FG, True)
        for bullet in s.bullets:
            cx = self.board.x + bullet.x * self.cell + self.cell // 2
            cy = self.board.y + bullet.y * self.cell + self.cell // 2
            self.screen.blit(
                self.sprite("bullet", self.cell, bullet.direction),
                (cx - self.cell // 2, cy - self.cell // 2),
            )
        now = pygame.time.get_ticks()
        self.fire_effects = [
            effect for effect in self.fire_effects if now - effect[3] < 120
        ]
        for x, y, direction, started in self.fire_effects:
            frame = min(3, (now - started) // 30)
            dx, dy = direction.value
            px = self.board.x + (x + dx * 0.45) * self.cell
            py = self.board.y + (y + dy * 0.45) * self.cell
            self.screen.blit(
                self.sprite(f"fire_{frame}", self.cell, direction), (px, py)
            )
        self.draw_tracers(now)
        if self.runner:
            for x, y in self.runner.draft.reserved:
                rect = pygame.Rect(
                    self.board.x + x * self.cell + 2,
                    self.board.y + y * self.cell + 2,
                    self.cell - 4,
                    self.cell - 4,
                )
                self.draw_rect(self.screen, (236, 203, 94), rect, 1)

    def draw_tracers(self, now):
        """One short moving arrow per shot; fade completely within 180 ms."""
        self.bullet_fades = [e for e in self.bullet_fades if now - e[5] < 180]
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(self.board)
        for x0, y0, x1, y1, direction, started in self.bullet_fades:
            elapsed = max(0, now - started)
            progress = min(1.0, elapsed / 110)
            frame = min(2, elapsed // 60)
            arrow = self.sprite(f"tracer_{frame}", self.cell, direction).copy()
            arrow.set_alpha(round(230 * (1 - elapsed / 180)))
            x = self.board.x + (x0 + (x1 - x0) * progress) * self.cell
            y = self.board.y + (y0 + (y1 - y0) * progress) * self.cell
            self.screen.blit(arrow, (round(x), round(y)))
        self.screen.set_clip(previous_clip)

    def draw_setup_panel(self):
        if not self.panel_open:
            self.button("Panel <", (1090, 16, 90, 32), self.toggle_panel)
            return
        x = 745
        self.draw_rect(self.screen, PANEL, (730, 0, 470, 784))
        self.text("SETUP", x, 20)
        self.button("Hide panel", (1050, 16, 130, 32), self.toggle_panel)
        self.text("01  MATCH SETTINGS", x, 60, (139, 184, 230), True)
        self.field("turns", "Max turns", (x, 105, 95, 32))
        self.field("budget", "AI budget (ms)", (x+110, 105, 130, 32))
        self.field("depth", "Depth", (x+255, 105, 70, 32))
        self.field("delay", "Delay ms", (x+340, 105, 95, 32))
        self.button(f'Timer: {"ON" if self.limit else "OFF"}', (x, 148, 130, 30),
                    lambda: setattr(self, "limit", not self.limit), self.limit)
        self.button(f'Nemesis: {"ON" if self.nemesis else "OFF"}', (x+140, 148, 145, 30),
                    self.toggle_nemesis, self.nemesis)
        self.button(f'Player first: {"ON" if self.player_priority else "OFF"}', (x+295, 148, 140, 30),
                    lambda: self.defer(self.toggle_player_priority), self.player_priority)
        self.text("02  MAP & PLACEMENT", x, 204, (139, 184, 230), True)
        tools = [("Select","select"),("Base","base"),("Tank","tank"),("Wall","wall"),("Erase","erase")]
        for index,(title,tool) in enumerate(tools):
            self.button(title, (x+index*88, 235, 82, 32),
                        lambda t=tool:self.set_tool(t), self.tool == tool)
        self.button("Assign A", (x, 279, 100, 32), lambda:self.assign(0))
        self.button("Assign B", (x+110, 279, 100, 32), lambda:self.assign(1))
        self.button("Rotate", (x+220, 279, 100, 32), self.rotate)
        self.button("START", (x+330, 275, 105, 40), self.start, style="primary")
        self.button("Load map...", (x, 329, 140, 36), self.load_terrain, style="info")
        self.button("Export map...", (x+150, 329, 140, 36), self.export_terrain, style="violet")
        self.button("Clear all", (x+300, 329, 135, 36), self.clear, style="danger")
        self.text("03  TANKS & AI", x, 393, (139, 184, 230), True)
        for index,tank in enumerate(self.state.tanks):
            mode = self.mode_by_id.get(tank.id, MODES[-1])
            mode_name = Path(mode[5:]).name if mode.startswith("file:") else MODE_LABELS[MODES.index(mode)]
            team = "?" if tank.team is None else "AB"[tank.team]
            self.button(f"T{tank.id} [{team}] HP {tank.hp} | {mode_name}",
                        (x, 425+index*34, 435, 29),
                        lambda tid=tank.id:setattr(self, "selected", tid), self.selected == tank.id)
        self.button("Cycle selected AI", (x, 575, 205, 34), self.cycle_mode)
        self.button("Load .py for tank", (x+215, 575, 220, 34), self.load_bot)
        self.text("Place 2 bases; assign every tank to A or B.", x, 641, MUTED, True)
        self.text("Export saves terrain only (walls).", x, 670, MUTED, True)
        self.text("START begins the match immediately.", x, 715, FG, True)

    def draw_match_hud(self):
        runner = self.runner
        self.screen.blit(self.turn_font.render(
            f"TURN #{self.state.turn} / {self.state.max_turns}", True, FG), (265, 18))
        self.button("Take control", (20, 65, 140, 36),
                    lambda: self.defer(self.take_control), style="info")
        self.button("Return to AI", (170, 65, 140, 36),
                    lambda: self.defer(lambda: self.control(None)), style="violet")
        self.button("Resume" if runner.paused else "Pause", (320, 65, 105, 36),
                    lambda: self.defer(self.pause_resume),
                    style="primary" if runner.paused else "warning")
        self.text("Control: AI" if runner.human is None else f"Control: T{runner.human}",
                  445, 72, MUTED, True)

    def draw_panel(self):
        if not self.runner:
            return self.draw_setup_panel()
        if not self.panel_open:
            self.button("Panel <", (1090, 16, 90, 32), self.toggle_panel)
            return
        x = 745
        self.draw_rect(self.screen, PANEL, (730, 0, 470, 784))
        self.text("MATCH", x, 20)
        self.button("Hide panel", (1050, 16, 130, 32), self.toggle_panel)

        def section(title, y, height):
            self.draw_rect(self.screen, (24, 32, 45), (x-4, y, 443, height), border_radius=9)
            self.text(title, x+9, y+10, (139, 184, 230), True)

        section("01  MATCH SETTINGS", 60, 132)
        self.field("budget", "AI budget / turn (ms)", (x+9, 113, 175, 30))
        self.field("depth", "Depth", (x+194, 113, 105, 30))
        self.field("delay", "Turn delay", (x+309, 113, 115, 30))
        self.button(f'Timer: {"ON" if self.limit else "OFF"}', (x+9, 153, 112, 28),
                    lambda: setattr(self, "limit", not self.limit), self.limit)
        self.button(f'Nemesis: {"ON" if self.nemesis else "OFF"}', (x+131, 153, 143, 28),
                    self.toggle_nemesis, self.nemesis)
        self.button(f'Player first: {"ON" if self.player_priority else "OFF"}',
                    (x+284, 153, 140, 28),
                    lambda: self.defer(self.toggle_player_priority), self.player_priority)

        section("02  MATCH ACTIONS", 205, 122)
        self.button("One turn", (x+9, 246, 112, 32), lambda: self.defer(self.step))
        self.button("Reset match", (x+131, 246, 143, 32),
                    lambda: self.defer(self.reset_match), style="warning")
        self.button("Back to setup", (x+284, 246, 140, 32),
                    lambda: self.defer(self.reset), style="violet")
        self.button("Apply timer / budget", (x+9, 288, 220, 28),
                    lambda: self.defer(self.apply_budget), style="info")
        self.text(f"AI: {self.runner.last_ai_spent_ms:.1f} ms", x+244, 294, MUTED, True)

        section("03  TANKS & SEARCH", 340, 350)
        for index, tank in enumerate(self.state.tanks):
            mode = self.mode_by_id.get(tank.id, MODES[-1])
            mode_name = Path(mode[5:]).name if mode.startswith("file:") else MODE_LABELS[MODES.index(mode)]
            team = "?" if tank.team is None else "AB"[tank.team]
            self.button(f"T{tank.id} [{team}]  HP {tank.hp} | {mode_name}",
                        (x+9, 380+index*34, 415, 29),
                        lambda tid=tank.id: setattr(self, "selected", tid), self.selected == tank.id)
        self.text("Click a tank above or on the map, then Take control.", x+9, 526, MUTED, True)
        if self.selected is not None:
            agent = self.runner.agents.get(self.selected)
            result = getattr(agent, "last_result", None)
            action = self.runner.last_actions.get(self.selected)
            self.text(f"T{self.selected} action: {action.name if action else '-'}", x+9, 556, FG, True)
            if result:
                stats = result.stats
                self.text(f"Depth {stats.completed_depth} | Nodes {stats.nodes}", x+9, 583, MUTED, True)
                self.text(f"Timeout: {stats.timed_out}", x+9, 607, MUTED, True)
        self.button("Compare + charts", (x+9, 643, 415, 34),
                    lambda: self.defer(self.benchmark), style="info")
        self.text("WASD/arrows: move | Space: fire | X: stay", x, 714, MUTED, True)
        self.text("P: pause/resume | Esc: pause", x, 742, MUTED, True)

    def draw_result(self, outcome):
        # Snapshot in logical coordinates also works with the high-DPI Qt canvas.
        native = self.screen.surface if hasattr(self.screen, "surface") else self.screen
        snapshot = pygame.transform.scale(native, CANVAS_SIZE).subsurface(self.board).copy()
        tiny = pygame.transform.smoothscale(snapshot,
            (max(1, self.board.width//12), max(1, self.board.height//12)))
        blurred = pygame.transform.smoothscale(tiny, self.board.size)
        shade = pygame.Surface(self.board.size, pygame.SRCALPHA)
        shade.fill((7, 12, 22, 185))
        blurred.blit(shade, (0, 0))
        self.screen.blit(blurred, self.board)
        card = pygame.Rect(0, 0, min(540, self.board.width-20), 265)
        card.center = self.board.center
        self.draw_rect(self.screen, (25, 35, 51), card, border_radius=16)
        winner = outcome.winner
        headline = "DRAW" if winner is None else f"TEAM {'AB'[winner]} WINS"
        color = (238, 205, 127) if winner is None else COLORS[winner]
        heading = self.result_font.render(headline, True, color)
        self.screen.blit(heading, heading.get_rect(center=(card.centerx, card.y+58)))
        reason = {"base_destroyed": "Base destroyed",
                  "all_tanks_destroyed": "All opposing tanks destroyed",
                  "turn_limit": "Turn limit reached",
                  "mutual_destruction": "Both teams destroyed"}.get(outcome.reason, "Match finished")
        detail = self.small.render(reason, True, MUTED)
        self.screen.blit(detail, detail.get_rect(center=(card.centerx, card.y+110)))
        if self.runner.human is not None and winner is not None:
            team = self.state.tank(self.runner.human).team
            text = self.action_font.render("VICTORY" if team == winner else "DEFEAT", True, FG)
            self.screen.blit(text, text.get_rect(center=(card.centerx, card.y+150)))
        # The result card is modal: clicks cannot activate controls underneath.
        self.buttons = []
        self.field_rects = {}
        width = (card.width-60)//2
        self.button("Play again", (card.x+20, card.bottom-66, width, 40),
                    lambda: self.defer(self.reset_match), style="primary")
        self.button("Back to setup", (card.x+40+width, card.bottom-66, width, 40),
                    lambda: self.defer(self.reset), style="violet")

    def toggle_player_priority(self):
        self.player_priority = not self.player_priority
        if self.runner:
            self.runner.set_player_priority(self.player_priority)
        self.message = (
            "Player wins new empty-cell contests; accepted actions stay locked."
            if self.player_priority
            else "All tanks use equal random cell contests."
        )

    def toggle_nemesis(self):
        self.nemesis = not self.nemesis
        if self.runner:
            runner = self.runner
            self.defer(
                lambda: [
                    setattr(a, "use_nemesis", self.nemesis)
                    for a in runner.agents.values()
                    if isinstance(a, SearchAgent)
                ]
            )

    def clear(self):
        self.setup = MatchSetup(parse_map("\n".join(["." * 13] * 11)))
        self.mode_by_id.clear()
        self.selected = None
        self.geometry()

    def draw_charts(self):
        self.draw_rect(self.screen, BG, (0, 0, 730, 780))
        self.text("Search comparison (3 repeats)", 25, 25)
        self.button(
            "Terminal scenarios",
            (25, 65, 180, 32),
            lambda: setattr(self, "bench_suite", "terminal"),
            self.bench_suite == "terminal",
        )
        self.button(
            "Same budget",
            (215, 65, 150, 32),
            lambda: setattr(self, "bench_suite", "budget"),
            self.bench_suite == "budget",
        )
        self.button("Close", (600, 65, 90, 32), lambda: setattr(self, "overlay", False))
        rows = [r for r in self.bench_rows if r.suite == self.bench_suite]
        for index, (attribute, title) in enumerate(
            [
                ("mean_ms", "Decision time: mean +/- SD (ms)"),
                ("mean_nodes", "Explored nodes"),
                ("mean_depth", "Completed depth"),
            ]
        ):
            y = 120 + index * 175
            self.text(title, 25, y)
            maximum = max((getattr(r, attribute) for r in rows), default=1) or 1
            for j, row in enumerate(rows):
                yy = y + 30 + j * 29
                value = getattr(row, attribute)
                self.text(MODE_LABELS[MODES.index(row.mode)], 25, yy, MUTED, True)
                width = max(1, int(285 * value / maximum))
                self.draw_rect(
                    self.screen,
                    [COLORS[0], COLORS[1], (136, 201, 132), (199, 157, 245)][j],
                    (220, yy + 3, width, 16),
                )
                label = f"{value:.1f}" + (
                    f" +/-{row.std_ms:.1f}" if attribute == "mean_ms" else ""
                )
                self.text(label, 515, yy - 1, small=True)
        y = 660
        for row in rows:
            self.text(
                f"{MODE_LABELS[MODES.index(row.mode)]}: timeout {row.timeouts}/{row.samples}, fallback {row.fallbacks}",
                25,
                y,
                MUTED,
                True,
            )
            y += 23
        self.text(
            "Timeout samples are included. Budget suite is per decision, not a match turn.",
            25,
            760,
            MUTED,
            True,
        )

    def draw(self):
        self.screen.fill(BG)
        self.buttons = []
        self.field_rects = {}
        self.screen.blit(self.title.render("TANK BATTLE", True, FG), (20, 20))
        self.draw_board()
        if self.panel_open and not self.runner:
            self.text(
                "Right-click selects a tank. Neutral tanks must be assigned before Start.",
                20,
                700,
                MUTED,
                True,
            )
            self.text(
                "Bases, tanks, walls and bullets use pixel art sprites.",
                20,
                725,
                MUTED,
                True,
            )
        if self.runner:
            self.draw_match_hud()
        self.draw_panel()
        result = self.runner.rules.outcome(self.state) if self.runner else None
        if result is not None:
            self.draw_result(result)
        elif self.overlay:
            self.draw_charts()
        self.draw_rect(self.screen, (12, 17, 24), (0, 784, 1200, 36))
        message = (
            "AI computing... " if self.future and self.job == "collect" else ""
        ) + self.message
        self.text(message[:145], 15, 791, (255, 220, 140), True)
        pygame.display.flip()

    def close(self):
        if self.runner:
            self.runner.cancel_event.set()
        self.cancel_benchmark.set()
        self.executor.shutdown(wait=True, cancel_futures=True)

    def run(self):
        try:
            while self.running:
                self.poll_worker()
                for event in pygame.event.get():
                    self.handle(event)
                self.notify(self.tick_match)
                self.draw()
                self.clock.tick(60)
        finally:
            self.close()


def enable_windows_dpi_awareness():
    if sys.platform != "win32":
        return
    import ctypes

    try:
        user32 = ctypes.windll.user32
        set_context = user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_bool
        if set_context(ctypes.c_void_p(-2)):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


def run(screen=None, clock=None):
    """Launcher entry: returns without quitting the launcher's pygame instance."""
    if screen is None and not pygame.display.get_init():
        enable_windows_dpi_awareness()
    pygame.init()
    app = Playground(screen)
    if clock is not None:
        app.clock = clock
    app.run()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    try:
        run()
    finally:
        pygame.quit()


