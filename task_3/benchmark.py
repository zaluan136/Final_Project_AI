from dataclasses import asdict
import json

from .boards import BOARDS
from .solver import KakuroSolver


def main():
    results = []
    for board in BOARDS:
        solver = KakuroSolver(board)
        solution = solver.solve()
        results.append({
            "board": board.name,
            "variables": len(board.variables),
            "runs": len(board.runs),
            "valid": solution is not None and solver.csp.is_solution(solution),
            **asdict(solver.statistics),
        })
    print(json.dumps(results, indent=2))
    return 0 if all(result["valid"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
