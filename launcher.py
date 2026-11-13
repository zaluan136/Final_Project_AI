"""Group launcher for the three AI final-project tasks."""

from __future__ import annotations

import importlib.util
import sys

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui import MATERIAL_QSS, set_button_icon
from task_3 import KakuroWidget


def label(text: str, object_name: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setWordWrap(True)
    if object_name:
        widget.setObjectName(object_name)
    return widget


def message_page(title: str, message: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(36, 36, 36, 36)
    layout.addWidget(label(title, "title"))
    layout.addWidget(label(message, "muted"))
    layout.addStretch()
    return page


def task_one_page() -> QWidget:
    """Load Task 1 only through its clean public package API."""
    try:
        from task_1 import NQueensPage
    except (ImportError, ModuleNotFoundError) as exc:
        return message_page(
            "Task 1 - N-Queens",
            "Task 1 chưa cung cấp package `task_1` với API `NQueensPage`. "
            "Sau khi module hóa đúng cấu trúc, launcher sẽ tự nhúng trang tại đây.\n\n"
            f"Chi tiết hiện tại: {exc}",
        )
    return NQueensPage(embedded=True)


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Introduction to Artificial Intelligence - Final Project")
        self.resize(1360, 850)
        self.setMinimumSize(1050, 680)

        self.task_two = QProcess(self)
        self.task_two.setProgram(sys.executable)
        self.task_two.setArguments(["-m", "task_2"])
        self.task_two.errorOccurred.connect(self._task_two_error)

        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(20, 28, 20, 20)
        navigation.setSpacing(10)
        navigation.addWidget(label("FINAL PROJECT", "title"))
        navigation.addWidget(label("GROUP 9", "eyebrow"))
        navigation.addSpacing(18)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._home_page())
        self.pages.addWidget(task_one_page())
        self.pages.addWidget(KakuroWidget())

        self.nav_buttons: list[QPushButton] = []
        for title, icon_name, page_index in (
            ("General", "home", 0),
            ("Task 1 - N-Queens", "queen", 1),
            ("Task 3 - Kakuro", "grid", 2),
        ):
            button = QPushButton(title)
            button.setObjectName("nav")
            set_button_icon(button, icon_name)
            button.clicked.connect(lambda _, index=page_index: self.show_page(index))
            navigation.addWidget(button)
            self.nav_buttons.append(button)

        task_two_button = QPushButton("Task 2 - Tank Battle")
        task_two_button.setObjectName("nav")
        set_button_icon(task_two_button, "game")
        task_two_button.clicked.connect(self.open_task_two)
        navigation.addWidget(task_two_button)
        navigation.addStretch()
        navigation.addWidget(label("524H0098 - 524H0101 - 524H0109"))

        shell.addWidget(sidebar)
        shell.addWidget(self.pages, 1)
        self.show_page(0)

    def _home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)
        layout.addWidget(label("Introduction to Artificial Intelligence", "pageTitle"))
        layout.addWidget(label("Chọn một task ở thanh điều hướng để bắt đầu.", "muted"))

        for title, description in (
            ("Task 1 - N-Queens", "SAT Solver và Min-Conflicts"),
            ("Task 2 - Tank Battle", "Chạy trong tiến trình và cửa sổ riêng"),
            (
                "Task 3 - Kakuro CSP",
                "Backtracking, MRV, Degree, LCV và Forward Checking",
            ),
        ):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(22, 19, 22, 19)
            card_layout.addWidget(label(title, "cardTitle"))
            card_layout.addWidget(label(description, "muted"))
            layout.addWidget(card)
        layout.addStretch()
        return page

    def show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setProperty("active", button_index == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def open_task_two(self) -> None:
        if self.task_two.state() != QProcess.ProcessState.NotRunning:
            return
        if importlib.util.find_spec("task_2") is None:
            QMessageBox.information(
                self,
                "Task 2 chưa sẵn sàng",
                "Launcher đang chờ entry point `python -m task_2`.",
            )
            return
        self.task_two.start()

    def _task_two_error(self, _error: QProcess.ProcessError) -> None:
        QMessageBox.warning(self, "Không thể mở Task 2", self.task_two.errorString())

    def closeEvent(self, event) -> None:
        if self.task_two.state() != QProcess.ProcessState.NotRunning:
            self.task_two.terminate()
            if not self.task_two.waitForFinished(1500):
                self.task_two.kill()
                self.task_two.waitForFinished(500)
        super().closeEvent(event)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MATERIAL_QSS)
    window = LauncherWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
