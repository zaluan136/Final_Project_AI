# N-Queens Studio (PySide6)

## Run

```bash
python -m pip install -r requirements.txt
python app.py
```

## Structure

- `app.py`: N-Queens interface, chessboard, and background solver workers
- `sat.py`: CNF encodings and complete Glucose3 SAT solver
- `core.py`: Min-Conflicts local search and independent solution verifier
- `test_core.py`: core unit tests

## Solver notes

- SAT/Glucose3 is complete: it returns a verified solution or proves the instance unsatisfiable.
- Min-Conflicts follows the CSP local-search algorithm from the lecture slides. It is fast on many large boards, but has a finite step/restart limit and may not find a solution on every run.
- The interface checks each returned placement before displaying it.
- CNF construction, solver setup, solver time, and total wall time are reported separately.
- Solver work runs outside the GUI thread. The chessboard is drawn with QPainter.
- PySAT is required for SAT solving.

## Academic note

The final-project handout in this repository states that AI tools may not be used for submitted work. Follow your instructor's rules when using this reference project.
