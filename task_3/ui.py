from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui import set_button_icon

from .boards import BOARDS
from .solver import KakuroSolver, SolverEvent


class BoardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = None
        self.current_event: SolverEvent | None = None
        self.setMinimumSize(270, 270)

    def set_board(self, board):
        self.board = board
        self.current_event = None
        self.update()

    def board_geometry(self):
        if self.board is None:
            return 0.0, 0.0, 0.0
        size = min((self.width() - 2) / self.board.width,
                   (self.height() - 2) / self.board.height, 120.0)
        return size, (self.width() - size * self.board.width) / 2, (self.height() - size * self.board.height) / 2

    def paintEvent(self, paint_event):
        if self.board is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        active = self.current_event.cell if self.current_event else None
        related = set()
        if active is not None:
            for run in self.board.cell_runs[active]:
                related.update(run.cells)
                related.add(run.clue)
        size, offset_x, offset_y = self.board_geometry()
        for r, row in enumerate(self.board.grid):
            for c, cell in enumerate(row):
                position = (r, c)
                rect = QRectF(offset_x + c * size, offset_y + r * size, size, size)
                shade = (
                    "#d9d9d9"
                    if cell.kind != "cell"
                    else ("#ededed" if position in related else "#ffffff")
                )
                painter.fillRect(rect, QColor(shade))
                painter.setPen(QPen(QColor("#111111"), 1))
                painter.drawRect(rect)
                if cell.kind != "cell":
                    painter.drawLine(rect.topLeft(), rect.bottomRight())
                    painter.setFont(QFont("Arial", max(8, int(size * 0.18)), QFont.Weight.Bold))
                    if cell.across is not None:
                        painter.drawText(
                            rect.adjusted(size / 2, 5, -6, -size / 2),
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                            str(cell.across),
                        )
                    if cell.down is not None:
                        painter.drawText(
                            rect.adjusted(6, size / 2, -size / 2, -5),
                            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                            str(cell.down),
                        )
                    continue
                assignment = self.current_event.assignment if self.current_event else {}
                if position in assignment:
                    painter.setFont(QFont("Arial", max(10, int(size * 0.35)), QFont.Weight.Bold))
                    painter.drawText(
                        rect, Qt.AlignmentFlag.AlignCenter, str(assignment[position])
                    )
                else:
                    domain = (
                        self.current_event.domains[position]
                        if self.current_event
                        else range(1, 10)
                    )
                    painter.setFont(QFont("Arial", max(6, int(size * 0.14))))
                    for value in domain:
                        x = (value - 1) % 3
                        y = (value - 1) // 3
                        small = QRectF(
                            rect.x() + x * size / 3,
                            rect.y() + y * size / 3,
                            size / 3,
                            size / 3,
                        )
                        painter.drawText(
                            small, Qt.AlignmentFlag.AlignCenter, str(value)
                        )
                    if not domain:
                        painter.setFont(QFont("Arial", 22))
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "∅")
                if position == active:
                    painter.setPen(QPen(QColor("#111111"), 3))
                    painter.drawRect(rect.adjusted(2, 2, -2, -2))


class KakuroWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kakuro - Constraint Satisfaction Problem")
        self.setObjectName("root")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.board_picker = QComboBox()
        self.board_picker.addItems([board.name for board in BOARDS])
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("primary")
        self.pause_button = QPushButton("Pause")
        self.step_button = QPushButton("Step")
        self.reset_button = QPushButton("Reset")
        set_button_icon(self.run_button, "play")
        set_button_icon(self.pause_button, "pause")
        set_button_icon(self.step_button, "next")
        set_button_icon(self.reset_button, "reset")
        self.speed = QComboBox()
        for label, interval in (("0.5×", 400), ("1×", 200), ("2×", 100), ("4×", 50)):
            self.speed.addItem(label, interval)
        self.speed.setCurrentIndex(1)
        self.board_view = BoardView()
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.run_details = QLabel()
        self.run_details.setWordWrap(True)
        self.statistics_label = QLabel()
        self.statistics_label.setWordWrap(True)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1200)
        inspector = QFrame()
        inspector.setObjectName("panel")
        inspector.setMinimumWidth(300)
        sidebar = QVBoxLayout(inspector)
        sidebar.setContentsMargins(20, 20, 20, 20)
        sidebar.setSpacing(12)
        method = QLabel("Controls")
        method.setObjectName("section")
        sidebar.addWidget(method)
        sidebar.addWidget(QLabel("Board"))
        sidebar.addWidget(self.board_picker)
        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addWidget(self.pause_button)
        sidebar.addLayout(actions)
        actions2 = QHBoxLayout()
        actions2.addWidget(self.step_button)
        actions2.addWidget(self.reset_button)
        sidebar.addLayout(actions2)
        sidebar.addWidget(QLabel("Speed"))
        sidebar.addWidget(self.speed)
        sidebar.addSpacing(8)
        activity = QLabel("Progress")
        activity.setObjectName("section")
        sidebar.addWidget(activity)
        self.status.setObjectName("status")
        sidebar.addWidget(self.status)
        sidebar.addWidget(self.run_details)
        sidebar.addWidget(self.statistics_label)
        sidebar.addWidget(self.log, 1)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        board_panel = QFrame()
        board_panel.setObjectName("card")
        board_layout = QVBoxLayout(board_panel)
        board_layout.setContentsMargins(20, 20, 20, 20)
        board_title = QLabel("Kakuro Board")
        board_title.setObjectName("section")
        board_layout.addWidget(board_title)
        board_layout.addWidget(self.board_view, 1)
        self.splitter.addWidget(board_panel)
        self.splitter.addWidget(inspector)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([650, 430])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        title = QLabel("Kakuro")
        title.setObjectName("heading")
        layout.addWidget(title)
        subtitle = QLabel("Backtracking - Forward Checking - MRV - Degree - LCV")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        layout.addWidget(self.splitter, 1)
        self.run_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.step_button.clicked.connect(self.step)
        self.reset_button.clicked.connect(self.reset)
        self.board_picker.currentIndexChanged.connect(self.reset)
        self.speed.currentIndexChanged.connect(self.update_speed)
        self.reset()

    def update_speed(self):
        self.timer.setInterval(int(self.speed.currentData()))

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

    def reset(self):
        self.timer.stop()
        if hasattr(self, "iterator"):
            self.iterator.close()
        board = BOARDS[self.board_picker.currentIndex()]
        self.solver = KakuroSolver(board)
        self.iterator = self.solver.events()
        self.finished = False
        self.board_view.set_board(board)
        self.status.setText("Ready. Select Run or Step to begin.")
        self.run_details.setText(
            f"{len(board.variables)} variables · {len(board.runs)} run constraints"
        )
        self.statistics_label.setText(
            "Solver time: 0 s\nBranches: 0 · Backtracks: 0 · Pruned: 0"
        )
        self.log.clear()
        self.update_speed()
        self.update_controls()

    def update_controls(self):
        self.run_button.setEnabled(not self.finished and not self.timer.isActive())
        self.pause_button.setEnabled(self.timer.isActive())
        self.step_button.setEnabled(not self.finished and not self.timer.isActive())

    def start(self):
        if not self.finished:
            self.timer.start()
            self.update_controls()

    def pause(self):
        self.timer.stop()
        self.update_controls()

    def step(self):
        self.pause()
        self.advance()

    def advance(self):
        if self.finished:
            return
        try:
            event = next(self.iterator)
        except StopIteration:
            self.finished = True
            self.pause()
            return
        self.board_view.current_event = event
        self.board_view.update()
        prefix = ""
        if event.cell is not None:
            r, c = event.cell
            prefix = f"R{r + 1}C{c + 1}: "
            runs = self.solver.csp.board.cell_runs[event.cell]
            details = []
            for run in runs:
                values = [
                    event.assignment[cell]
                    for cell in run.cells
                    if cell in event.assignment
                ]
                details.append(f"{run.label} · assigned sum: {sum(values)}/{run.total}")
            self.run_details.setText("\n".join(details))
        self.status.setText(prefix + event.message)
        labels = {
            "start": "START",
            "select": "SELECT",
            "try": "TRY",
            "prune": "PRUNE",
            "failure": "FAILURE",
            "restore": "BACKTRACK",
            "complete": "COMPLETE",
        }
        depth = len(event.assignment)
        self.log.appendPlainText(
            f"[{labels[event.kind]}] {prefix}{depth} assigned\n{event.message}\n"
        )
        statistics = event.statistics
        self.statistics_label.setText(
            f"Solver time: {statistics.elapsed:.4f} s\n"
            f"Branches: {statistics.branches} · Backtracks: {statistics.backtracks} · Pruned: {statistics.pruned}"
        )
        if event.kind == "complete":
            self.finished = True
            self.iterator.close()
            self.pause()
