"""N-Queens Studio: standalone PySide6 frontend, independent of group launcher."""
from __future__ import annotations
import csv
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QFrame, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QComboBox, QSpinBox, QCheckBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QSizePolicy, QScrollArea
)

from core import verify_solution
from sat import SATSolver, CNFEncoder
from core import MinConflictsSolver
from experiments import sat_experiments, local_experiments, export_csv

BG = '#0B1020'
SURFACE = '#121B2E'
CARD = '#17243B'
STROKE = '#293A54'
INK = '#F7FAFF'
MUTED = '#C0D0E5'
BLUE = '#4C9AFF'
GREEN = '#51D3A2'

STYLES = '''
QMainWindow, QWidget#root { background: #0B1020; color: #F7FAFF; }
QWidget { color: #F7FAFF; font-family: 'Segoe UI'; font-size: 13px; }
QFrame#panel, QFrame#card { background: #17243B; border: 1px solid #293A54; border-radius: 15px; }
QFrame#sidebar { background: #111A2D; border-right: 1px solid #293A54; }
QLabel#muted { color: #C0D0E5; }
QLabel#heading { font-size: 26px; font-weight: 800; color: #FFFFFF; }
QLabel#stat { font-size: 26px; font-weight: 800; color: #FFFFFF; }
QLabel#section { font-size: 16px; font-weight: 700; color: #FFFFFF; }
QPushButton { background: #243751; border: 1px solid #405675; border-radius: 10px; color: #FFFFFF; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #344A6A; border-color: #70B1FF; }
QPushButton:pressed { background: #17243B; }
QPushButton:disabled { color: #8292A7; background: #202B3D; border-color: #27374E; }
QPushButton#primary { background: #3689F6; border-color: #3689F6; color: #FFFFFF; }
QPushButton#primary:hover { background: #60A5FA; }
QPushButton#navigation { background: transparent; border: 1px solid transparent; text-align: left; padding: 14px; }
QPushButton#navigation[active="true"] { background: #223A5C; border: 1px solid #487EBA; }
QComboBox, QSpinBox { background: #0F1B30; color: white; border: 1px solid #526780; border-radius: 9px; padding: 9px; min-height: 23px; }
QComboBox QAbstractItemView { background: #17243B; color: white; selection-background-color: #2E73C8; }
QSpinBox::up-button, QSpinBox::down-button { width: 20px; }
QCheckBox { spacing: 10px; color: white; }
QTableWidget { background: #121B2E; alternate-background-color: #1D2C43; gridline-color: #2A3D54; color: white; border: 1px solid #293A54; border-radius: 9px; }
QHeaderView::section { background: #253958; color: #FFFFFF; padding: 10px; border: 0; font-weight: bold; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #111A2D; width: 10px; }
QScrollBar::handle:vertical { background: #415A79; border-radius: 5px; }
'''


def text(s: str, kind: str = '', size: int | None = None) -> QLabel:
    lbl = QLabel(s)
    if kind:
        lbl.setObjectName(kind)
    if size:
        f = lbl.font(); f.setPointSize(size); lbl.setFont(f)
    lbl.setWordWrap(True)
    return lbl


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(); frame.setObjectName('card')
    box = QVBoxLayout(frame); box.setContentsMargins(18, 18, 18, 18); box.setSpacing(10)
    return frame, box


class Chessboard(QWidget):
    """Paint squares and queens directly; render at high DPI, no OS glyph dependency."""
    def __init__(self):
        super().__init__()
        self.n = 8
        self.queens = None
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_solution(self, n: int, queens: list[int] | None):
        self.n, self.queens = n, queens
        self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = max(1, min(self.width(), self.height()) - 18)
        x0 = (self.width() - side) / 2
        y0 = (self.height() - side) / 2
        cell = side / self.n
        for row in range(self.n):
            for col in range(self.n):
                p.fillRect(round(x0 + col * cell), round(y0 + row * cell),
                           round(x0 + (col + 1) * cell) - round(x0 + col * cell),
                           round(y0 + (row + 1) * cell) - round(y0 + row * cell),
                           QColor('#F4E9D5' if (row + col) % 2 == 0 else '#83AA98'))
        if self.queens:
            font = QFont('DejaVu Sans', max(7, int(cell * 0.58)))
            font.setWeight(QFont.Weight.Bold)
            p.setFont(font)
            for col, row in enumerate(self.queens):
                rect_x = x0 + col * cell
                rect_y = y0 + row * cell
                # Outline against both square colors, then queen symbol.
                from PySide6.QtCore import QRectF
                rect = QRectF(rect_x, rect_y, cell, cell)
                p.setPen(QColor('#FFFFFF'))
                p.drawText(rect.translated(1.5, 1.5), Qt.AlignmentFlag.AlignCenter, '♛')
                p.setPen(QColor('#1B2841'))
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, '♛')
        p.end()


class SolveWorker(QThread):
    completed = Signal(object, float, str)
    failed = Signal(str)

    def __init__(self, n, method, encoding, symmetry, heuristic, seed, steps):
        super().__init__()
        self.args = (n, method, encoding, symmetry, heuristic, seed, steps)

    def run(self):
        n, method, encoding, symmetry, heuristic, seed, steps = self.args
        try:
            started = perf_counter()
            if method == 'SAT / Glucose3':
                result = SATSolver(n, encoding, symmetry).solve()
                family = 'SAT'
            else:
                result = MinConflictsSolver(n, heuristic, max_steps=steps,
                                           max_restarts=20, seed=seed).solve()
                family = 'LOCAL'
            wall_ms = (perf_counter() - started) * 1000
            self.completed.emit(result, wall_ms, family)
        except Exception as exc:
            self.failed.emit(f'{type(exc).__name__}: {exc}')


class BenchWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, ns, trials, family):
        super().__init__(); self.ns, self.trials, self.family = ns, trials, family

    def run(self):
        try:
            rows = (sat_experiments(self.ns, trials=self.trials)
                    if self.family == 'SAT' else local_experiments(self.ns, trials=self.trials))
            self.completed.emit(rows)
        except Exception as exc:
            self.failed.emit(f'{type(exc).__name__}: {exc}')


class NQueensPage(QWidget):
    """Importable game page: parent launcher can add this widget to QStackedWidget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('root')
        self._worker = None
        self._bench_worker = None
        self._clock_start = None
        self._bench_rows = []
        self._clock = QTimer(self)
        self._clock.setInterval(8)  # best-effort UI refresh; not a guaranteed 120 FPS
        self._clock.timeout.connect(self._tick)
        self._build()

    def _build(self):
        root = QHBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(236)
        nav = QVBoxLayout(sidebar); nav.setContentsMargins(18, 27, 18, 18); nav.setSpacing(12)
        nav.addWidget(text('♛  AI GAME LAB', 'heading', 18))
        nav.addWidget(text('TASK 01  /  N-QUEENS', 'muted', 10))
        nav.addSpacing(24)
        self.nav_buttons = []
        for label, index in [('♛    Solve & Visualize', 0), ('▤    CNF Analysis', 1), ('◷    Benchmark', 2)]:
            btn = QPushButton(label); btn.setObjectName('navigation'); btn.setProperty('active', index == 0)
            btn.clicked.connect(lambda _, i=index: self._go(i))
            nav.addWidget(btn); self.nav_buttons.append(btn)
        nav.addStretch(1)
        nav.addWidget(text('Designed for group integration', 'muted', 10))
        nav.addWidget(text('N-Queens · Tank Battle · Kakuro', 'muted', 9))
        root.addWidget(sidebar)
        main = QWidget(); main.setObjectName('root')
        ml = QVBoxLayout(main); ml.setContentsMargins(28, 22, 28, 22); ml.setSpacing(18)
        header = QHBoxLayout()
        titlecol = QVBoxLayout(); titlecol.setSpacing(2)
        titlecol.addWidget(text('N-Queens Studio', 'heading'))
        titlecol.addWidget(text('SAT solving, CNF encoding & local search experiments', 'muted'))
        header.addLayout(titlecol); header.addStretch()
        ml.addLayout(header)
        self.pages = QStackedWidget()
        ml.addWidget(self.pages, 1)
        self._solve_page(); self._cnf_page(); self._bench_page()
        root.addWidget(main, 1)

    def _go(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty('active', i == index)
            btn.style().unpolish(btn); btn.style().polish(btn)
        if index == 1: self._update_cnf()

    def _control(self, layout, label, widget):
        layout.addWidget(text(label, 'muted', 11)); layout.addWidget(widget)

    def _solve_page(self):
        page = QWidget(); outer = QHBoxLayout(page); outer.setContentsMargins(0,0,0,0); outer.setSpacing(18)
        controls, cl = card(); controls.setFixedWidth(292)
        cl.addWidget(text('Solver configuration', 'section'))
        self.n = QSpinBox(); self.n.setRange(4, 256); self.n.setValue(8)
        self._control(cl, 'Board size (N)', self.n)
        self.alg = QComboBox(); self.alg.addItems(['SAT / Glucose3', 'Min-Conflicts'])
        self._control(cl, 'Algorithm', self.alg)
        self.encoding = QComboBox(); self.encoding.addItems(['pairwise', 'seqcounter', 'ladder'])
        self._control(cl, 'SAT encoding', self.encoding)
        self.symmetry = QCheckBox('Break mirror symmetry'); cl.addWidget(self.symmetry)
        self.heuristic = QComboBox(); self.heuristic.addItems(['standard', 'most_conflicted'])
        self._control(cl, 'Local variable heuristic', self.heuristic)
        self.seed = QSpinBox(); self.seed.setRange(0, 9999999); self.seed.setValue(42)
        self._control(cl, 'Random seed', self.seed)
        self.steps = QSpinBox(); self.steps.setRange(50, 10000000); self.steps.setValue(5000)
        self._control(cl, 'Max steps per restart', self.steps)
        cl.addStretch(1)
        self.solve_btn = QPushButton('▶    Solve N-Queens'); self.solve_btn.setObjectName('primary')
        self.solve_btn.clicked.connect(self._solve)
        cl.addWidget(self.solve_btn)
        self.clear_btn = QPushButton('Reset board'); self.clear_btn.clicked.connect(self._reset)
        cl.addWidget(self.clear_btn)
        outer.addWidget(controls)

        content = QWidget(); cr = QVBoxLayout(content); cr.setContentsMargins(0,0,0,0); cr.setSpacing(14)
        statrow = QHBoxLayout(); statrow.setSpacing(12)
        self.wall = self._stat(statrow, 'Elapsed (wall)', '—', 'ms')
        self.solve_time = self._stat(statrow, 'Solver time', '—', 'ms')
        self.clauses = self._stat(statrow, 'CNF clauses', '—', '')
        self.variables = self._stat(statrow, 'Variables', '—', '')
        cr.addLayout(statrow)
        boardcard, bc = card()
        top = QHBoxLayout(); top.addWidget(text('Chessboard', 'section')); top.addStretch()
        self.board_status = text('Ready to solve', 'muted'); top.addWidget(self.board_status)
        bc.addLayout(top)
        self.board = Chessboard(); bc.addWidget(self.board, 1)
        self.details = text('Choose an algorithm and press Solve.', 'muted', 11)
        bc.addWidget(self.details)
        cr.addWidget(boardcard, 1)
        outer.addWidget(content, 1)
        self.pages.addWidget(page)
        self.alg.currentIndexChanged.connect(self._toggle_options)
        self._toggle_options()

    def _stat(self, row, title, initial, unit):
        f, box = card()
        box.addWidget(text(title, 'muted', 10))
        value = text(initial, 'stat')
        box.addWidget(value)
        if unit: box.addWidget(text(unit, 'muted', 9))
        row.addWidget(f, 1)
        return value

    def _toggle_options(self):
        sat = self.alg.currentIndex() == 0
        self.encoding.setEnabled(sat); self.symmetry.setEnabled(sat)
        self.heuristic.setEnabled(not sat); self.seed.setEnabled(not sat); self.steps.setEnabled(not sat)

    def _tick(self):
        if self._clock_start is not None:
            self.wall.setText(f'{(perf_counter()-self._clock_start)*1000:,.3f}')

    def _solve(self):
        if self._worker and self._worker.isRunning(): return
        self._reset()
        self._clock_start = perf_counter()
        self._clock.start()
        self.solve_btn.setEnabled(False)
        self.board_status.setText('Solving…')
        self._worker = SolveWorker(self.n.value(), self.alg.currentText(),
                                   self.encoding.currentText(), self.symmetry.isChecked(),
                                   self.heuristic.currentText(), self.seed.value(), self.steps.value())
        self._worker.completed.connect(self._solved)
        self._worker.failed.connect(self._failed)
        self._worker.start()

    def _stop(self, wall_ms=None):
        self._clock.stop(); self._clock_start = None
        self.solve_btn.setEnabled(True)
        if wall_ms is not None: self.wall.setText(f'{wall_ms:,.3f}')

    def _solved(self, result, wall_ms, family):
        self._stop(wall_ms)
        n = self.n.value()
        queens = result.queens if result.success and verify_solution(result.queens, n) else None
        self.board.set_solution(n, queens)
        self.board_status.setText('✓ Valid solution' if queens else 'No solution found')
        if family == 'SAT':
            self.solve_time.setText(f'{result.solve_ms:,.3f}')
            self.clauses.setText(f'{result.cnf.num_clauses:,}')
            self.variables.setText(f'{result.cnf.num_vars:,}')
            self.details.setText(f'CNF build {result.cnf.build_ms:.3f} ms · Solver setup {result.setup_ms:.3f} ms · Actual SAT solve {result.solve_ms:.3f} ms')
        else:
            self.solve_time.setText(f'{result.elapsed_ms:,.3f}')
            self.clauses.setText('N/A'); self.variables.setText('N/A')
            self.details.setText(f'Steps: {result.steps:,} · Restarts: {result.restarts} · Heuristic: {result.strategy}')

    def _failed(self, message):
        self._stop()
        self.board_status.setText('Solver error')
        self.details.setText(message)
        QMessageBox.warning(self, 'Solver error', message)

    def _reset(self):
        if self._worker and self._worker.isRunning(): return
        self._clock.stop(); self._clock_start = None
        self.wall.setText('—'); self.solve_time.setText('—')
        self.clauses.setText('—'); self.variables.setText('—')
        self.board.set_solution(self.n.value(), None)
        self.board_status.setText('Ready to solve')
        self.details.setText('Wall time includes the worker lifecycle; solver time measures the algorithm itself.')

    def _cnf_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(16)
        f, box = card()
        box.addWidget(text('CNF Encoding Explorer', 'section'))
        box.addWidget(text('Each square is a Boolean variable. The figures below are the theoretical pairwise clause counts.', 'muted'))
        row = QHBoxLayout(); row.addWidget(text('Board size N:'))
        self.cnf_n = QSpinBox(); self.cnf_n.setRange(4, 256); self.cnf_n.setValue(8)
        self.cnf_n.valueChanged.connect(self._update_cnf)
        row.addWidget(self.cnf_n); row.addStretch(); box.addLayout(row)
        self.cnf_stats = text('', '', 13); self.cnf_stats.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.cnf_stats)
        box.addWidget(text('Exact-one in every row = one positive clause + at-most-one. Columns require only at-most-one. Diagonals also use at-most-one.', 'muted'))
        layout.addWidget(f)
        note, nb = card()
        nb.addWidget(text('CNF construction explained', 'section'))
        nb.addWidget(text('At least one in a row:  X₁₁ ∨ X₁₂ ∨ ... ∨ X₁ₙ', '', 14))
        nb.addWidget(text('At most one among attacking squares:  ¬Xᵢⱼ ∨ ¬Xₖₗ', '', 14))
        nb.addWidget(text('For other encodings (Sequential Counter / Ladder), auxiliary variables and clause counts are generated by PySAT. Select them in Solve, or compare using Benchmark.', 'muted'))
        layout.addWidget(note); layout.addStretch()
        self.pages.addWidget(page)
        self._update_cnf()

    def _update_cnf(self):
        n = self.cnf_n.value()
        rowcol = n*n*(n-1)
        diagonals = n*(n-1)*(2*n-1)//3
        total = n + rowcol + diagonals
        self.cnf_stats.setText(f'Original variables: {n*n:,}\n'
                               f'At-least-one row clauses: {n:,}\n'
                               f'Pairwise row + column clauses: {rowcol:,}\n'
                               f'Pairwise diagonal clauses: {diagonals:,}\n'
                               f'Total pairwise clauses: {total:,}')

    def _bench_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(14)
        top, box = card(); box.addWidget(text('Benchmark Laboratory', 'section'))
        box.addWidget(text('Repeated experiments on the same N values. CSV export available.', 'muted'))
        row = QHBoxLayout()
        row.addWidget(text('Family:'))
        self.b_family = QComboBox(); self.b_family.addItems(['SAT', 'LOCAL']); row.addWidget(self.b_family)
        row.addWidget(text('Trials:'))
        self.b_trials = QSpinBox(); self.b_trials.setRange(1, 100); self.b_trials.setValue(5); row.addWidget(self.b_trials)
        row.addWidget(text('N preset:'))
        self.b_ns = QComboBox(); self.b_ns.addItems(['4,8,12,16', '8,20,50,100', '16,32,64']); row.addWidget(self.b_ns)
        row.addStretch(); box.addLayout(row)
        brow = QHBoxLayout()
        self.b_run = QPushButton('▶   Run benchmark'); self.b_run.setObjectName('primary'); self.b_run.clicked.connect(self._run_bench)
        self.b_export = QPushButton('Export CSV'); self.b_export.setEnabled(False); self.b_export.clicked.connect(self._export)
        brow.addWidget(self.b_run); brow.addWidget(self.b_export); brow.addStretch(); box.addLayout(brow)
        self.b_status = text('No experiment running.', 'muted'); box.addWidget(self.b_status)
        layout.addWidget(top)
        result, rb = card(); rb.addWidget(text('Experiment results', 'section'))
        cols = ['Family', 'N', 'Method', 'Trials', 'Success', 'Variables', 'Clauses', 'Mean solve (ms)', 'Mean total (ms)', 'Median (ms)']
        self.b_table = QTableWidget(0, len(cols)); self.b_table.setHorizontalHeaderLabels(cols)
        self.b_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.b_table.setAlternatingRowColors(True); self.b_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        rb.addWidget(self.b_table)
        layout.addWidget(result, 1)
        self.pages.addWidget(page)

    def _run_bench(self):
        if self._bench_worker and self._bench_worker.isRunning(): return
        ns = tuple(map(int, self.b_ns.currentText().split(',')))
        self.b_run.setEnabled(False); self.b_export.setEnabled(False)
        self.b_status.setText('Running experiments…')
        self._bench_worker = BenchWorker(ns, self.b_trials.value(), self.b_family.currentText())
        self._bench_worker.completed.connect(self._bench_done)
        self._bench_worker.failed.connect(self._bench_failed)
        self._bench_worker.start()

    def _bench_done(self, rows):
        self._bench_rows = rows
        self.b_run.setEnabled(True); self.b_export.setEnabled(True)
        self.b_status.setText(f'Completed {len(rows)} configurations. Results measured on this machine.')
        self.b_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r.family, str(r.n), r.method, str(r.trials), str(r.successful),
                    str(r.variables) if r.variables is not None else 'N/A',
                    str(r.clauses) if r.clauses is not None else 'N/A',
                    f'{r.solve_ms:.3f}' if r.solve_ms is not None else 'N/A',
                    f'{r.total_ms:.3f}', f'{r.median_ms:.3f}']
            for j, val in enumerate(vals): self.b_table.setItem(i, j, QTableWidgetItem(val))

    def _bench_failed(self, message):
        self.b_run.setEnabled(True)
        self.b_status.setText('Benchmark error: '+message)
        QMessageBox.warning(self, 'Benchmark error', message)

    def _export(self):
        if not self._bench_rows: return
        path, _ = QFileDialog.getSaveFileName(self, 'Save benchmark', 'nqueens_benchmark.csv', 'CSV files (*.csv)')
        if path: export_csv(path, self._bench_rows)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('N-Queens Studio | AI Game Lab')
        self.resize(1480, 900)
        self.setMinimumSize(1120, 710)
        self.setCentralWidget(NQueensPage(self))


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLES)
    window = MainWindow(); window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
