# Task 2 - Tank Battle

A turn-based tank game using adversarial search, with a Pygame interface. Play against the AI or watch AI-controlled tanks compete.

Run from the `source` directory:

```bash
python -m pip install -r task_2/requirements.txt
python -m task_2
```

Alternatively, install the project requirements and select Task 2 in `python launcher.py`.

## Start a match

1. Select **Load map...** and choose a file from `task_2/maps/`, or build a map in the editor.
2. Place two bases and two to four tanks, and assign each tank to team A or B.
3. Choose a search algorithm for each tank and select **START**.

The supplied maps include a 1v1 and a 2v2 setup. Map symbols are `.` for empty cells, `#` for walls, `A` and `B` for bases, and `a` and `b` for tanks. Map export saves terrain only.

## Controls and rules

- Select a tank and use **Take control** to play, or **Return to AI** to hand it back.
- Move with WASD or arrow keys, fire with Space, and stay with X. Use P to pause or resume.
- A tank moves at most one cell per turn. Bullets move up to three cells per cycle, checking collisions at each cell.
- Tanks, bases and walls start with 6, 9 and 3 HP. Hits deal one damage; friendly bases absorb friendly bullets without damage.
- A team loses when one of its tanks or its base is destroyed. Simultaneous losses draw. The turn limit is configurable.

## Search and benchmarks

The four configurations are Minimax, Alpha-Beta, Heuristic Minimax, and Heuristic Minimax with Alpha-Beta. Search uses a time budget and can fall back to a legal action. **Compare + charts** runs shared scenarios and reports timing, search nodes, completed depth, timeouts and fallbacks. Node counts are not counts of unique states.

```bash
python -m task_2.benchmark
python -m unittest discover -s task_2 -p "test*.py"
```

External agents can be integrated through `match/bot_loader.py` and the `choose_action(state, tank_id, draft, deadline)` interface. See `match/example_bot.py`. The UI does not currently provide a Python bot import button, and an independent group's bot has not been verified.

## Files

- `core/`: game state and rules.
- `search/`: search algorithms, evaluation and agents.
- `match/`: match setup, runner and external bot interface.
- `play.py` and `qt_widget.py`: Pygame interface and launcher integration.
- `maps/` and `asset/`: maps and sprites.
