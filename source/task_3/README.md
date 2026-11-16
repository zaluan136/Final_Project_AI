# Task 3 - Kakuro CSP

Visualize Kakuro solving with backtracking, forward checking, MRV, degree tie-breaking and LCV. The supplied boards are a 5x5 example and a 9x9 complex test case.

Run from the `source` directory:

```bash
python -m pip install -r task_3/requirements.txt
python -m task_3
```

Alternatively, install the project requirements and select Task 3 in `python launcher.py`.

## Usage

Choose a board and use **Run**, **Pause**, **Step** or **Reset**. The speed slider controls playback. Small numbers show remaining domain values; large numbers show assignments. The side panel displays the current event, progress and search history.

Each white cell is a variable with an initial domain of 1 to 9. Each horizontal and vertical run must sum to its clue and contain distinct values. The solver stops at the first valid solution; it does not prove uniqueness or implement AC-3.

## Files and tests

- `model.py` and `boards.py`: CSP model and board definitions.
- `boards/`: reference HTML boards.
- `solver.py`: search and visualization events.
- `ui.py`: PySide6 interface.
- `benchmark.py`: solver statistics.

```bash
python -m unittest discover -s task_3/tests -v
python -m task_3.benchmark
```
