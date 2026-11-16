# Task 1 - N-Queens

Solve and visualize N-Queens using Glucose3 SAT or Min-Conflicts. The PySide6 interface also provides CNF analysis and benchmarks.

Run from the `source` directory:

```bash
python -m pip install -r task_1/requirements.txt
python -m task_1
```

Alternatively, install the project requirements and select Task 1 in `python launcher.py`.

## Usage

- **Solve**: choose the board size and algorithm, then select **Solve N-Queens**.
- **CNF analysis**: inspect pairwise encoding counts.
- **Benchmark**: compare configurations and export results to CSV.

Min-Conflicts uses bounded steps and restarts. Failure within the limit does not prove that a board has no solution. Solver time and total elapsed time are measured separately.

## Files and tests

- `app.py`: interface and workers.
- `core.py`: Min-Conflicts and solution validation.
- `sat.py`: CNF encoding and SAT solver.
- `experiments.py`: benchmarks and CSV export.

```bash
python -m unittest discover -s task_1/tests -v
```
