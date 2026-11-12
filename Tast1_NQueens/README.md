# N-Queens Studio (PySide6) — study/reference project

## Run

```bash
python -m pip install -r requirements.txt
python app.py
```

## Structure

- `app.py`: high-contrast PySide6 interface, navigation, workers, elapsed time
- `sat.py`: CNF encoders and Glucose3 solver
- `core.py`: Min-Conflicts + solution verifier
- `experiments.py`: benchmark and CSV
- `test_core.py`: independent core unit tests

## UI notes

- For real SAT tests, PySAT must be installed.
- Solver time, CNF build, solver initialization, and overall wall time are distinct measurements.
- The timer *requests* a refresh every 8 ms; Qt does not guarantee 120 visible FPS.
- Workers run outside the GUI thread so solving does not block interactions.
- `NQueensPage` is a QWidget and may be inserted into the group's launcher `QStackedWidget`.
- The chessboard directly uses QPainter rather than static images.

## Academic note

The provided final-project handout prohibits use of AI tools in the submitted project. This package is educational reference material and should not be submitted as AI-generated work.
