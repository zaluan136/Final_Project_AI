from .model import Board, Cell, KakuroCSP, Run
from .solver import KakuroSolver

__all__ = ["Board", "Cell", "KakuroCSP", "Run", "KakuroSolver", "KakuroWidget"]


def __getattr__(name):
    if name == "KakuroWidget":
        from .ui import KakuroWidget
        return KakuroWidget
    raise AttributeError(name)
