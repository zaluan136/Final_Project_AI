"""Pygame playground. Run: python -m Task2.play.

The engine stays independent of pygame.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event
from time import perf_counter

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = 'Task2'

import pygame

from Task2.search.agents import CONFIGURATIONS, SearchAgent
from .benchmark import compare
from Task2.match.bot_loader import FileAgent
from Task2.match.runner import MatchConfig, MatchRunner
from Task2.core.rules import GameRules
from Task2.match.setup import MatchSetup, export_map, load_map, parse_map
from Task2.core.state import Action, Direction, Wall

COLORS = [(74, 169, 255), (255, 112, 105)]
BG, PANEL, FG, MUTED = (20, 25, 34), (30, 38, 50), (229, 235, 244), (157, 171, 190)
MODE_LABELS = ['Minimax', 'Alpha-Beta', 'Heuristic Minimax', 'Heuristic + AB']
MODES = list(CONFIGURATIONS)
KEY_ACTION = {pygame.K_w: Action.MOVE_UP, pygame.K_UP: Action.MOVE_UP,
              pygame.K_s: Action.MOVE_DOWN, pygame.K_DOWN: Action.MOVE_DOWN,
              pygame.K_a: Action.MOVE_LEFT, pygame.K_LEFT: Action.MOVE_LEFT,
              pygame.K_d: Action.MOVE_RIGHT, pygame.K_RIGHT: Action.MOVE_RIGHT,
              pygame.K_SPACE: Action.FIRE, pygame.K_x: Action.STAY}


class Playground:
    def __init__(self, screen=None):
        self.screen = screen or pygame.display.set_mode((1200, 820))
        pygame.display.set_caption('Tank Battle | temporary playground')
        self.font = pygame.font.SysFont('segoeui', 18)
        self.small = pygame.font.SysFont('segoeui', 15)
        self.action_font = pygame.font.SysFont('segoeui', 16, bold=True)
        self.title = pygame.font.SysFont('segoeui', 25, bold=True)
        self.clock = pygame.time.Clock()
        self.asset_dir = Path(__file__).resolve().parent / 'Asset'
        self.sprites = {path.stem: pygame.image.load(str(path)).convert_alpha()
                        for path in self.asset_dir.glob('*.png')}
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
        self.setup = MatchSetup(parse_map('\n'.join(['.'*13]*11)))
        self.selected = None
        self.tool = 'select'
        self.mode_by_id = {}
        self.nemesis = True
        self.limit = True
        self.player_priority = True
        self.fields = {'turns': '300', 'budget': '950', 'depth': '2', 'delay': '400',
                       'path': '', 'map_name': ''}
        self.active_field = None
        self.select_all_text = False
        self.field_rects = {}
        self.buttons = []
        self.message = 'Place two bases and 2-4 tanks. Select a tank, then assign A/B.'
        self.last_step = 0
        self.single_step = False
        self.overlay = False
        self.bench_suite = 'terminal'
        self.bench_rows = []
        self.geometry()

    def geometry(self):
        state = self.state
        width = 690 if self.panel_open else self.screen.get_width()-40
        height = 610 if self.panel_open else self.screen.get_height()-130
        limit = 52 if self.panel_open else max(width, height)
        self.cell = max(1, min(limit, width//state.width, height//state.height))
        self.board = pygame.Rect(0, 0, self.cell*state.width, self.cell*state.height)
        self.board.center = (20+width//2, 75+height//2)

    @property
    def state(self):
        return self.runner.state if self.runner else self.setup.state

    def number(self, name):
        value = int(self.fields[name])
        if value < (0 if name == 'delay' else 1):
            raise ValueError(f'{name} is invalid')
        return value

    def notify(self, action):
        try:
            action()
        except Exception as error:
            self.message = str(error)

    def text(self, text, x, y, color=FG, small=False):
        surface = (self.small if small else self.font).render(str(text), True, color)
        self.screen.blit(surface, (x, y))

    def button(self, label, rect, callback, active=False, style='neutral'):
        rect = pygame.Rect(rect)
        palettes = {
            'neutral': ((56, 69, 87), (39, 49, 65), (85, 102, 125)),
            'primary': ((36, 143, 100), (22, 100, 73), (92, 218, 164)),
            'info': ((46, 112, 183), (29, 76, 132), (108, 178, 245)),
            'warning': ((156, 101, 35), (110, 66, 24), (243, 184, 93)),
            'danger': ((158, 65, 71), (113, 40, 48), (232, 125, 133)),
            'violet': ((113, 86, 169), (76, 55, 126), (183, 153, 237)),
        }
        top, bottom, border = palettes['info' if active and style == 'neutral' else style]
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            ratio = y/max(1, rect.height-1)
            color = tuple(min(255, round(a+(b-a)*ratio)+(14 if hovered else 0))
                          for a, b in zip(top, bottom))
            pygame.draw.line(surface, color, (0, y), (rect.width-1, y))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=6)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(surface, rect)
        pygame.draw.rect(self.screen, border, rect, 2 if active or hovered else 1, border_radius=6)
        font = self.action_font if style != 'neutral' else self.small
        text = font.render(str(label), True, (250, 252, 255))
        position = text.get_rect(center=rect.center) if style != 'neutral' else text.get_rect(midleft=(rect.x+9, rect.centery))
        self.screen.blit(text, position)
        self.buttons.append((rect, callback))

    def field(self, name, label, rect):
        rect = pygame.Rect(rect)
        self.text(label, rect.x, rect.y-20, MUTED, True)
        pygame.draw.rect(self.screen, (15, 21, 30), rect, border_radius=4)
        if name == self.active_field:
            pygame.draw.rect(self.screen, COLORS[0], rect, 1, border_radius=4)
        visible = self.fields[name]
        while self.small.size(visible)[0] > rect.width-14:
            visible = visible[1:]
        self.text(visible, rect.x+6, rect.y+6, small=True)
        self.field_rects[name] = rect

    def defer(self, action):
        """Pause/handoff at worker boundary; never mutate a busy runner."""
        if self.future is not None:
            self.after_job = action
            if self.runner:
                self.runner.cancel_event.set()
            self.cancel_benchmark.set()
            self.message = 'Stopping computation...'
        else:
            self.notify(action)

    def start(self):
        state = self.setup.start(self.number('turns'))
        self.match_initial_state = state
        self.new_match(state)

    def new_match(self, state):
        self.fire_effects.clear()
        self.bullet_fades.clear()
        rules = GameRules()
        agents = {}
        for tank in state.tanks:
            choice = self.mode_by_id.get(tank.id, 'heuristic_alpha_beta')
            if choice.startswith('file:'):
                agents[tank.id] = FileAgent(choice[5:], tank.id)
            else:
                agents[tank.id] = SearchAgent(rules, tank.id, choice, self.number('depth'),
                                            seed=tank.id, use_nemesis=self.nemesis)
        # Gameplay gets a fresh lottery each match; tests can still seed the runner.
        self.runner = MatchRunner(state, agents, MatchConfig(self.limit, self.number('budget')),
                                  player_priority_enabled=self.player_priority)
        self.runner.pause()
        self.message = 'Ready, paused. Resume or One turn. Select a tank to take control.'
        self.single_step = False
        self.geometry()

    def reset_match(self):
        if self.match_initial_state is None:
            raise ValueError('Start a match first')
        self.new_match(self.match_initial_state)
        self.message = 'Match reset to turn 0. Paused and ready to resume.'

    def toggle_panel(self):
        self.panel_open = not self.panel_open
        self.active_field = None
        if not self.panel_open:
            self.tool = 'select'
        self.geometry()

    def reset(self):
        self.runner = None
        self.match_initial_state = None
        self.fire_effects.clear()
        self.bullet_fades.clear()
        self.selected = None
        self.overlay = False
        self.single_step = False
        self.message = 'Back to setup; original placements restored.'
        self.geometry()

    def pause_resume(self):
        if self.runner:
            if self.runner.paused:
                self.runner.cancel_event.clear()
                self.runner.resume()
                self.message = 'Running. P pauses; click a tank and Take control to play.'
            else:
                self.runner.pause()
                self.message = 'Paused.'

    def step(self):
        if self.runner:
            self.runner.cancel_event.clear()
            self.runner.resume()
            self.single_step = True

    def control(self, tank_id):
        self.runner.control(tank_id)
        self.message = ('AI controls all tanks. Resume to continue.' if tank_id is None else
                        f'Control T{tank_id}. Resume; WASD/arrows, Space=fire, X=stay.')

    def take_control(self):
        if self.selected is None:
            raise ValueError('Select a living tank first')
        self.control(self.selected)

    def set_tool(self, tool):
        self.tool = tool

    def assign(self, team):
        if self.selected is None:
            raise ValueError('Select a tank first')
        self.setup.assign(self.selected, team)

    def rotate(self):
        if self.selected is None:
            raise ValueError('Select a tank first')
        directions = list(Direction)
        tank = self.setup.state.tank(self.selected)
        direction = directions[(directions.index(tank.direction)+1) % 4]
        self.setup.state = replace(self.setup.state, tanks=tuple(
            replace(t, direction=direction) if t.id == tank.id else t for t in self.setup.state.tanks))

    def cycle_mode(self):
        if self.selected is None:
            raise ValueError('Select a tank first')
        current = self.mode_by_id.get(self.selected, MODES[-1])
        self.mode_by_id[self.selected] = MODES[(MODES.index(current)+1) % 4] if current in MODES else MODES[0]

    def load_bot(self):
        if self.selected is None:
            raise ValueError('Select a tank first')
        chosen = self.choose_file(bot=True)
        if not chosen:
            return
        path = Path(chosen).resolve(strict=True)
        if path.suffix != '.py':
            raise ValueError('Choose a .py bot file')
        self.mode_by_id[self.selected] = 'file:'+str(path)
        self.message = f'T{self.selected}: external bot {path.name}'

    def choose_file(self, save=False, bot=False):
        """Native picker on the UI thread; cancelling leaves the setup intact."""
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
            folder = Path(__file__).resolve().parent
            maps = folder / 'maps'
            options = dict(parent=root,
                           initialdir=str(folder if bot or not maps.is_dir() else maps),
                           filetypes=[('Python bot', '*.py')] if bot else [('Text map', '*.txt')])
            if save:
                return filedialog.asksaveasfilename(title='Export terrain map',
                                                    defaultextension='.txt',
                                                    confirmoverwrite=True,
                                                    initialfile='my_map.txt', **options)
            return filedialog.askopenfilename(title='Choose bot' if bot else 'Choose map', **options)
        finally:
            root.destroy()
            # Discard clicks/keys generated while the native dialog was open.
            pygame.event.clear((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                pygame.KEYDOWN, pygame.KEYUP))

    def load_terrain(self):
        chosen = self.choose_file()
        if not chosen:
            return
        state = load_map(chosen)
        self.setup = MatchSetup(replace(state, tanks=(), bases=()))
        self.setup.state = state
        self.setup.next_id = max((t.id for t in state.tanks), default=-1)+1
        self.selected = None
        self.mode_by_id.clear()
        self.geometry()
        self.message = ('Preset loaded; ready to START or edit placements.' if state.tanks
                        else 'Map loaded; place bases and tanks yourself.')

    def export_terrain(self):
        chosen = self.choose_file(save=True)
        if not chosen:
            return
        target = Path(chosen)
        path = export_map(self.setup.state, target.name, target.parent, overwrite=True)
        self.message = f'Terrain map saved to {path}'

    def apply_budget(self):
        self.runner.configure(MatchConfig(self.limit, self.number('budget')))
        self.message = 'Budget changes apply next turn.'

    def board_click(self, position, right=False):
        x, y = (position[0]-self.board.x)//self.cell, (position[1]-self.board.y)//self.cell
        tank = next((t for t in self.state.alive if (t.x, t.y) == (x, y)), None)
        if self.runner or not self.panel_open or self.tool == 'select' or right:
            self.selected = tank.id if tank else None
            return
        if self.tool == 'base':
            self.setup.place_base(x, y)
        elif self.tool == 'tank':
            self.selected = self.setup.place_tank(x, y)
        elif self.tool == 'wall':
            self.setup.state = replace(self.setup.state, walls=self.setup.state.walls+(Wall(x, y),))
        elif self.tool == 'erase':
            if tank:
                self.setup.remove_tank(tank.id)
                if self.selected == tank.id:
                    self.selected = None
            base = next((b for b in self.setup.state.bases if (b.x, b.y) == (x, y)), None)
            if base:
                self.setup.remove_base(base.team)
            self.setup.state = replace(self.setup.state, walls=tuple(
                w for w in self.setup.state.walls if (w.x, w.y) != (x, y)))

    def benchmark(self):
        if self.runner:
            self.runner.pause()
        state = self.state
        state.validate_ready()
        if GameRules().outcome(state) is not None:
            raise ValueError('Benchmark from an unfinished game or setup')
        self.cancel_benchmark.clear()
        self.future = self.executor.submit(compare, state, min(950, self.number('budget')),
                                           self.number('depth'), 3, self.cancel_benchmark)
        self.job = 'benchmark'
        self.message = 'Comparing four algorithms on identical snapshots...'

    def poll_worker(self):
        if self.future is None or not self.future.done():
            return
        try:
            result = self.future.result()
            if self.job == 'benchmark':
                self.bench_rows = result
                self.overlay = True
                self.message = 'Terminal suite = final-turn scenarios; Budget suite = current snapshot.'
            elif self.runner and self.runner.events:
                self.message = self.runner.events[-1]
                self.runner.events = self.runner.events[-8:]
        except Exception as error:
            self.message = f'{type(error).__name__}: {error}'
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
            result = 'DRAW' if outcome.winner is None else f'Team {"AB"[outcome.winner]} wins'
            self.message = f'{result}: {outcome.reason}'
            return
        if runner.paused:
            return
        if runner.ready:
            if (perf_counter()-self.last_step)*1000 < self.number('delay'):
                return
            before = runner.state
            firing = [(t.x, t.y, t.direction) for t in runner.state.alive
                      if dict(runner.draft.accepted).get(t.id) is Action.FIRE]
            runner.commit()
            now = pygame.time.get_ticks()
            self.fire_effects = [(x, y, direction, now) for x, y, direction in firing]
            # Bullets advance up to three cells in execute(). Mark the end of
            # that travel, including shots absorbed by an entity or the edge.
            occupied = {(e.x, e.y) for e in (*before.tanks, *before.bases, *before.walls)
                        if e.hp > 0}
            fades = []
            for x, y, direction in [*( (b.x, b.y, b.direction) for b in before.bullets), *firing]:
                start_x, start_y = x, y
                dx, dy = direction.value
                for _ in range(3):
                    nx, ny = x+dx, y+dy
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
        waiting = runner.human in runner.draft.pending and runner.human not in runner.proposals
        other_pending = any(i != runner.human and i not in runner.proposals for i in runner.draft.pending)
        if waiting and not other_pending:
            self.message = f'T{runner.human}: choose an action (or retry). Space=fire, X=stay.'
            return
        runner.cancel_event.clear()
        self.future = self.executor.submit(runner.collect)
        self.job = 'collect'

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            if self.runner:
                self.runner.cancel_event.set()
            self.cancel_benchmark.set()
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
                if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_v and self.active_field == 'path':
                    pygame.scrap.init()
                    raw = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if raw:
                        pasted = raw.decode('utf-8', errors='ignore').replace('\x00', '').strip()
                        self.fields['path'] = ('' if self.select_all_text else self.fields['path'])+pasted
                        self.select_all_text = False
                    return
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    self.fields[self.active_field] = '' if self.select_all_text else self.fields[self.active_field][:-1]
                    self.select_all_text = False
                elif event.unicode.isprintable():
                    if self.active_field in ('path', 'map_name') or event.unicode.isdecimal():
                        if self.select_all_text:
                            self.fields[self.active_field] = ''
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
                self.defer(lambda: self.runner.submit(action))

    def sprite(self, name, size, direction=Direction.UP):
        key = (name, size, direction)
        if key not in self.scaled_sprites:
            image = self.sprites[name]
            angle = {Direction.UP: 0, Direction.RIGHT: -90,
                     Direction.DOWN: 180, Direction.LEFT: 90}[direction]
            if angle:
                image = pygame.transform.rotate(image, angle)
            self.scaled_sprites[key] = pygame.transform.scale(image, (size, size))
        return self.scaled_sprites[key]

    def draw_board(self):
        s = self.state
        for y in range(s.height):
            for x in range(s.width):
                rect = pygame.Rect(self.board.x+x*self.cell, self.board.y+y*self.cell, self.cell, self.cell)
                self.screen.blit(self.sprite('ground', self.cell), rect)
                pygame.draw.rect(self.screen, (38, 51, 43), rect, 1)
        def box(entity, inset=6):
            return pygame.Rect(self.board.x+entity.x*self.cell+inset,
                               self.board.y+entity.y*self.cell+inset,
                               max(1, self.cell-2*inset), max(1, self.cell-2*inset))
        for wall in s.walls:
            rect = box(wall, 0)
            self.screen.blit(self.sprite('wall', self.cell), rect)
            self.text(wall.hp, rect.x+3, rect.y+2, FG, True)
        for base in s.bases:
            if base.hp <= 0:
                continue
            rect = box(base, 0)
            self.screen.blit(self.sprite(f'base_{"ab"[base.team]}', self.cell), rect)
            pygame.draw.rect(self.screen, (20, 26, 30), (rect.x+2, rect.y+2, 29, 17))
            self.text(f'{"AB"[base.team]}:{base.hp}', rect.x+3, rect.y+2, FG, True)
        for tank in s.tanks:
            if tank.hp <= 0:
                continue
            rect = box(tank, 0)
            name = 'tank_neutral' if tank.team is None else f'tank_{"ab"[tank.team]}'
            self.screen.blit(self.sprite(name, self.cell, tank.direction), rect)
            center = rect.center
            if tank.id == self.selected:
                pygame.draw.rect(self.screen, FG, rect.inflate(8, 8), 2, border_radius=5)
            if self.runner and tank.id == self.runner.human:
                pygame.draw.circle(self.screen, (255, 220, 95), center, self.cell//2-2, 2)
            label = f'{"?" if tank.team is None else "AB"[tank.team]}{tank.id}'
            pygame.draw.rect(self.screen, (20, 26, 30), (rect.x+2, rect.y+2, 26, 17))
            self.text(label, rect.x+3, rect.y+2, FG, True)
            pygame.draw.rect(self.screen, (20, 26, 30), (rect.right-16, rect.bottom-18, 14, 16))
            self.text(tank.hp, rect.right-15, rect.bottom-19, FG, True)
        for bullet in s.bullets:
            cx = self.board.x+bullet.x*self.cell+self.cell//2
            cy = self.board.y+bullet.y*self.cell+self.cell//2
            self.screen.blit(self.sprite('bullet', self.cell, bullet.direction),
                             (cx-self.cell//2, cy-self.cell//2))
        now = pygame.time.get_ticks()
        self.fire_effects = [effect for effect in self.fire_effects if now-effect[3] < 120]
        for x, y, direction, started in self.fire_effects:
            frame = min(3, (now-started)//30)
            dx, dy = direction.value
            px = self.board.x+(x+dx*0.45)*self.cell
            py = self.board.y+(y+dy*0.45)*self.cell
            self.screen.blit(self.sprite(f'fire_{frame}', self.cell, direction), (px, py))
        self.draw_tracers(now)
        if self.runner:
            for x, y in self.runner.draft.reserved:
                rect = pygame.Rect(self.board.x+x*self.cell+2, self.board.y+y*self.cell+2, self.cell-4, self.cell-4)
                pygame.draw.rect(self.screen, (236, 203, 94), rect, 1)

    def draw_tracers(self, now):
        """One short moving arrow per shot; fade completely within 180 ms."""
        self.bullet_fades = [e for e in self.bullet_fades if now-e[5] < 180]
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(self.board)
        for x0, y0, x1, y1, direction, started in self.bullet_fades:
            elapsed = max(0, now-started)
            progress = min(1.0, elapsed/110)
            frame = min(2, elapsed//60)
            arrow = self.sprite(f'tracer_{frame}', self.cell, direction).copy()
            arrow.set_alpha(round(230*(1-elapsed/180)))
            x = self.board.x+(x0+(x1-x0)*progress)*self.cell
            y = self.board.y+(y0+(y1-y0)*progress)*self.cell
            self.screen.blit(arrow, (round(x), round(y)))
        self.screen.set_clip(previous_clip)

    def draw_panel(self):
        if not self.panel_open:
            self.button('Panel <', (self.screen.get_width()-110, 16, 90, 32), self.toggle_panel)
            if self.runner:
                self.text(f'Turn {self.state.turn}/{self.state.max_turns}', 260, 22, MUTED, True)
                self.button('Resume' if self.runner.paused else 'Pause', (420, 16, 100, 32),
                            lambda: self.defer(self.pause_resume),
                            style='primary' if self.runner.paused else 'warning')
            return
        x = 745
        pygame.draw.rect(self.screen, PANEL, (730, 0, 470, 820))
        self.text('SETUP' if not self.runner else 'MATCH', x, 20)
        self.button('Hide panel' if self.panel_open else 'Show panel',
                    (1050, 16, 130, 32), self.toggle_panel)
        self.field('turns', 'Max turns (setup)', (x, 75, 95, 32))
        self.field('budget', 'AI ms / all tanks', (x+110, 75, 130, 32))
        self.field('depth', 'Depth', (x+255, 75, 70, 32))
        self.field('delay', 'Delay ms', (x+340, 75, 95, 32))
        self.button(f'Timer: {"ON" if self.limit else "OFF"}', (x, 120, 145, 32),
                    lambda: setattr(self, 'limit', not self.limit), self.limit)
        self.button(f'Nemesis: {"ON" if self.nemesis else "OFF"}', (x+155, 120, 150, 32),
                    self.toggle_nemesis, self.nemesis)
        self.button(f'Player first: {"ON" if self.player_priority else "OFF"}',
                    (x+315, 120, 120, 32),
                    lambda: self.defer(self.toggle_player_priority), self.player_priority)
        if not self.runner:
            tools = [('Select', 'select'), ('Base', 'base'), ('Tank', 'tank'), ('Wall', 'wall'), ('Erase', 'erase')]
            for index, (label, tool) in enumerate(tools):
                self.button(label, (x+index*88, 170, 82, 32), lambda t=tool: self.set_tool(t), self.tool == tool)
            self.text('Place bases first; each base creates one team.', x, 214, MUTED, True)
            self.button('Assign A', (x, 245, 100, 32), lambda: self.assign(0))
            self.button('Assign B', (x+110, 245, 100, 32), lambda: self.assign(1))
            self.button('Rotate', (x+220, 245, 100, 32), self.rotate)
            self.button('START', (x+330, 242, 105, 40), self.start, style='primary')
        else:
            self.button('Resume' if self.runner.paused else 'Pause', (x, 170, 105, 38),
                        lambda: self.defer(self.pause_resume),
                        style='primary' if self.runner.paused else 'warning')
            self.button('One turn', (x+115, 170, 85, 38), lambda: self.defer(self.step))
            self.button('Back to setup', (x+210, 170, 145, 38), lambda: self.defer(self.reset), style='violet')
            self.button('Apply ms', (x+365, 170, 70, 38), lambda: self.defer(self.apply_budget))
            self.button('Take control', (x, 215, 140, 32), lambda: self.defer(self.take_control), style='info')
            self.button('Return to AI', (x+150, 215, 140, 32), lambda: self.defer(lambda: self.control(None)))
            self.button('Reset match', (x+300, 215, 135, 32), lambda: self.defer(self.reset_match), style='warning')
            self.text(f'Turn {self.state.turn}/{self.state.max_turns} | AI {self.runner.last_ai_spent_ms:.1f} ms', x, 260, MUTED, True)
        self.text('Tanks (click map or row to select)', x, 300, MUTED, True)
        for index, tank in enumerate(self.state.tanks):
            y = 326+index*34
            choice = self.mode_by_id.get(tank.id, MODES[-1])
            label = Path(choice[5:]).name if choice.startswith('file:') else MODE_LABELS[MODES.index(choice)]
            team = '?' if tank.team is None else 'AB'[tank.team]
            self.button(f'T{tank.id} [{team}] HP {tank.hp} | {label}', (x, y, 435, 29),
                        lambda tid=tank.id: setattr(self, 'selected', tid), self.selected == tank.id)
        if not self.runner:
            self.button('Cycle selected AI', (x, 475, 205, 32), self.cycle_mode)
            self.button('Load .py for tank', (x+215, 475, 220, 32), self.load_bot)
            self.text('Choose a map file or a folder to save terrain.', x, 535, MUTED, True)
            self.button('Load map...', (x, 565, 140, 40), self.load_terrain, style='info')
            self.button('Export map...', (x+150, 565, 140, 40), self.export_terrain, style='violet')
            self.button('Clear all', (x+300, 565, 135, 40), self.clear, style='danger')
            self.text('Export saves walls; bases and tanks are not included.', x, 615, MUTED, True)
        elif self.selected is not None:
            agent = self.runner.agents.get(self.selected)
            result = getattr(agent, 'last_result', None)
            if result:
                stats = result.stats
                self.text(f'Last search: depth {stats.completed_depth}, nodes {stats.nodes}', x, 480, MUTED, True)
                self.text(f'Timeout: {stats.timed_out} | Nemesis: {getattr(agent, "nemesis", None)}', x, 504, MUTED, True)
            action = self.runner.last_actions.get(self.selected)
            self.text(f'Last action: {action.name if action else "-"}', x, 533, MUTED, True)
            self.text(f'Fallback last turn: {sorted(self.runner.last_fallback_ids)}', x, 559, MUTED, True)
        if self.runner:
            self.button('Compare + charts', (x, 640, 205, 38), lambda: self.defer(self.benchmark), style='info')
        self.text('WASD/arrows: move | Space: fire | X: stay', x, 700, MUTED, True)
        self.text('P: pause/resume | Esc: pause / close charts', x, 724, MUTED, True)
        self.text('Pure Minimax may timeout; default uses heuristic.', x, 750, MUTED, True)

    def toggle_player_priority(self):
        self.player_priority = not self.player_priority
        if self.runner:
            self.runner.set_player_priority(self.player_priority)
        self.message = ('Player wins new empty-cell contests; accepted actions stay locked.'
                        if self.player_priority else 'All tanks use equal random cell contests.')

    def toggle_nemesis(self):
        self.nemesis = not self.nemesis
        if self.runner:
            self.defer(lambda: [setattr(a, 'use_nemesis', self.nemesis)
                                for a in self.runner.agents.values() if isinstance(a, SearchAgent)])

    def clear(self):
        self.setup = MatchSetup(parse_map('\n'.join(['.'*13]*11)))
        self.mode_by_id.clear()
        self.selected = None
        self.geometry()

    def draw_charts(self):
        pygame.draw.rect(self.screen, BG, (0, 0, 730, 780))
        self.text('Search comparison (3 repeats)', 25, 25)
        self.button('Terminal scenarios', (25, 65, 180, 32), lambda: setattr(self, 'bench_suite', 'terminal'), self.bench_suite == 'terminal')
        self.button('Same budget', (215, 65, 150, 32), lambda: setattr(self, 'bench_suite', 'budget'), self.bench_suite == 'budget')
        self.button('Close', (600, 65, 90, 32), lambda: setattr(self, 'overlay', False))
        rows = [r for r in self.bench_rows if r.suite == self.bench_suite]
        for index, (attribute, title) in enumerate([('mean_ms', 'Decision time: mean +/- SD (ms)'),
                                                   ('mean_nodes', 'Explored nodes'), ('mean_depth', 'Completed depth')]):
            y = 120+index*175
            self.text(title, 25, y)
            maximum = max((getattr(r, attribute) for r in rows), default=1) or 1
            for j, row in enumerate(rows):
                yy = y+30+j*29
                value = getattr(row, attribute)
                self.text(MODE_LABELS[MODES.index(row.mode)], 25, yy, MUTED, True)
                width = max(1, int(285*value/maximum))
                pygame.draw.rect(self.screen, [COLORS[0], COLORS[1], (136, 201, 132), (199, 157, 245)][j], (220, yy+3, width, 16))
                label = f'{value:.1f}' + (f' +/-{row.std_ms:.1f}' if attribute == 'mean_ms' else '')
                self.text(label, 515, yy-1, small=True)
        y = 660
        for row in rows:
            self.text(f'{MODE_LABELS[MODES.index(row.mode)]}: timeout {row.timeouts}/{row.samples}, fallback {row.fallbacks}', 25, y, MUTED, True)
            y += 23
        self.text('Timeout samples are included. Budget suite is per decision, not a match turn.', 25, 760, MUTED, True)

    def draw(self):
        self.screen.fill(BG)
        self.buttons = []
        self.field_rects = {}
        self.screen.blit(self.title.render('TANK BATTLE', True, FG), (20, 20))
        self.draw_board()
        if self.panel_open:
            self.text('Right-click selects a tank. Neutral tanks must be assigned before Start.', 20, 700, MUTED, True)
            self.text('Bases, tanks, walls and bullets use pixel art sprites.', 20, 725, MUTED, True)
        self.draw_panel()
        if self.overlay:
            self.draw_charts()
        pygame.draw.rect(self.screen, (12, 17, 24), (0, 784, 1200, 36))
        message = ('AI computing... ' if self.future and self.job == 'collect' else '')+self.message
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


def run(screen=None, clock=None):
    """Launcher entry: returns without quitting the launcher's pygame instance."""
    pygame.init()
    app = Playground(screen)
    if clock is not None:
        app.clock = clock
    app.run()


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        run()
    finally:
        pygame.quit()
