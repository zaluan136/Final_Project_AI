from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
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
        self.cell_size = 66

    def set_board(self, board):
        self.board = board
        self.current_event = None
        self.setFixedSize(
            board.width * self.cell_size + 1, board.height * self.cell_size + 1
        )
        self.update()

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
        size = self.cell_size
        for r, row in enumerate(self.board.grid):
            for c, cell in enumerate(row):
                position = (r, c)
                rect = QRectF(c * size, r * size, size, size)
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
                    painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
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
                    painter.setFont(QFont("Arial", 23, QFont.Weight.Bold))
                    painter.drawText(
                        rect, Qt.AlignmentFlag.AlignCenter, str(assignment[position])
                    )
                else:
                    domain = (
                        self.current_event.domains[position]
                        if self.current_event
                        else range(1, 10)
                    )
                    painter.setFont(QFont("Arial", 9))
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
        self.run_button = QPushButton("Chạy")
        self.run_button.setObjectName("primary")
        self.pause_button = QPushButton("Tạm dừng")
        self.step_button = QPushButton("Bước tiếp")
        self.reset_button = QPushButton("Đặt lại")
        set_button_icon(self.run_button, "play")
        set_button_icon(self.pause_button, "pause")
        set_button_icon(self.step_button, "next")
        set_button_icon(self.reset_button, "reset")
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(1, 100)
        self.speed.setValue(65)
        self.speed.setMinimumWidth(120)
        self.board_view = BoardView()
        scroll = QScrollArea()
        scroll.setWidget(self.board_view)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setMinimumSize(370, 370)
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
        inspector.setMinimumWidth(280)
        inspector.setMaximumWidth(360)
        sidebar = QVBoxLayout(inspector)
        sidebar.setContentsMargins(20, 20, 20, 20)
        sidebar.setSpacing(12)
        method = QLabel("Điều khiển")
        method.setObjectName("section")
        sidebar.addWidget(method)
        sidebar.addWidget(QLabel("Bàn chơi"))
        sidebar.addWidget(self.board_picker)
        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addWidget(self.pause_button)
        sidebar.addLayout(actions)
        actions2 = QHBoxLayout()
        actions2.addWidget(self.step_button)
        actions2.addWidget(self.reset_button)
        sidebar.addLayout(actions2)
        sidebar.addWidget(QLabel("Tốc độ"))
        sidebar.addWidget(self.speed)
        sidebar.addSpacing(8)
        activity = QLabel("Tiến trình")
        activity.setObjectName("section")
        sidebar.addWidget(activity)
        self.status.setObjectName("status")
        sidebar.addWidget(self.status)
        sidebar.addWidget(self.run_details)
        sidebar.addWidget(self.statistics_label)
        sidebar.addWidget(self.log, 1)
        content = QHBoxLayout()
        content.setSpacing(16)
        board_panel = QFrame()
        board_panel.setObjectName("card")
        board_layout = QVBoxLayout(board_panel)
        board_layout.setContentsMargins(20, 20, 20, 20)
        board_title = QLabel("Bàn Kakuro")
        board_title.setObjectName("section")
        board_layout.addWidget(board_title)
        board_layout.addWidget(scroll, 1)
        legend = QLabel("Số nhỏ: domain  ·  Số lớn: đã gán  ·  Viền đậm: ô đang xét")
        legend.setObjectName("muted")
        legend.setWordWrap(True)
        board_layout.addWidget(legend)
        content.addWidget(board_panel, 1)
        content.addWidget(inspector)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        title = QLabel("Kakuro")
        title.setObjectName("heading")
        layout.addWidget(title)
        subtitle = QLabel("Backtracking · Forward Checking · MRV · Degree · LCV")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        layout.addLayout(content, 1)
        self.run_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.step_button.clicked.connect(self.step)
        self.reset_button.clicked.connect(self.reset)
        self.board_picker.currentIndexChanged.connect(self.reset)
        self.speed.valueChanged.connect(self.update_speed)
        self.reset()

    def update_speed(self):
        self.timer.setInterval(max(1, (101 - self.speed.value()) * 6))

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
        self.status.setText("Sẵn sàng. Chọn Chạy hoặc Bước tiếp.")
        self.run_details.setText(
            f"{len(board.variables)} biến - {len(board.runs)} ràng buộc dãy"
        )
        self.statistics_label.setText(
            "Thời gian solver: 0 s - Thử: 0 - Backtrack: 0 - Loại: 0"
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
                details.append(f"{run.label} - đã gán {sum(values)}/{run.total}")
            self.run_details.setText("\n".join(details))
        self.status.setText(prefix + event.message)
        labels = {
            "start": "BẮT ĐẦU",
            "select": "CHỌN Ô",
            "try": "GÁN THỬ",
            "prune": "FORWARD CHECKING",
            "failure": "THẤT BẠI",
            "restore": "BACKTRACK",
            "complete": "KẾT THÚC",
        }
        depth = len(event.assignment)
        self.log.appendPlainText(
            f"[{labels[event.kind]}] Đã gán {depth} ô - {prefix}{event.message}\n"
        )
        statistics = event.statistics
        self.statistics_label.setText(
            f"Thời gian solver: {statistics.elapsed:.4f} s\n"
            f"Thử: {statistics.branches} - Backtrack: {statistics.backtracks} - Loại: {statistics.pruned}"
        )
        if event.kind == "complete":
            self.finished = True
            self.iterator.close()
            self.pause()
