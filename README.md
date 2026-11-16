# Introduction to Artificial Intelligence - Final Project

[GitHub repository](https://github.com/zaluan136/Final_Project_AI)

The project contains three applications:

- [N-Queens](source/task_1/README.md): N-Queens with SAT and Min-Conflicts.
- [Tank Battle](source/task_2/README.md): Tank Battle with adversarial search and Pygame.
- [Kakuro](source/task_3/README.md): Kakuro with constraint propagation and backtracking.

Each task directory contains its own README. The project root also contains [report.pdf](report.pdf) and [demo.txt](demo.txt).

## Setup

Use Python 3.12. Open a terminal in the project root and enter the source directory:

```bash
cd source
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

Run these commands from `source/`:

```bash
python launcher.py
```

To run a task separately:

```bash
python -m task_1
python -m task_2
python -m task_3
```

## Test

```bash
python -m unittest discover -v
```


