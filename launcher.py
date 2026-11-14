from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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

from ui import set_button_icon
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

        self.task_two = None

        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(20, 28, 20, 20)
        navigation.setSpacing(10)
        navigation.addWidget(label("AI PROJECT", "brand"))
        navigation.addWidget(label("INTRODUCTION TO AI  /  GROUP 9", "eyebrow"))
        navigation.addSpacing(18)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._home_page())
        self.pages.addWidget(task_one_page())
        self.pages.addWidget(self._task_two_page())
        self.pages.addWidget(KakuroWidget())

        self.nav_buttons: list[QPushButton] = []
        for title, icon_name, page_index in (
            ("General", "home", 0),
            ("Task 1 - N-Queens", "queen", 1),
            ("Task 2 - Tank Battle", "game", 2),
            ("Task 3 - Kakuro", "grid", 3),
        ):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            set_button_icon(button, icon_name)
            button.clicked.connect(lambda _, index=page_index: self.show_page(index))
            navigation.addWidget(button)
            self.nav_buttons.append(button)

        navigation.addStretch()
        navigation.addWidget(label("524H0098  -  524H0101  -  524H0109", "muted"))

        shell.addWidget(sidebar)
        shell.addWidget(self.pages, 1)
        self.show_page(0)

    def _home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)
        layout.addWidget(label("Introduction to Artificial Intelligence", "pageTitle"))
        layout.addWidget(
            label("Tổng quan các bài toán và phương pháp trong dự án.", "muted")
        )
        layout.addSpacing(12)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        for title, description in (
            ("01   N-Queens", "SAT Solver và Min-Conflicts"),
            ("02   Tank Battle", "Pygame - màn hình trò chơi"),
            (
                "03   Kakuro CSP",
                "Backtracking, MRV, Degree, LCV và Forward Checking",
            ),
        ):
            card = QFrame()
            card.setObjectName("card")
            card.setFixedHeight(190)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(24, 24, 24, 24)
            card_layout.setSpacing(12)
            card_layout.addWidget(label(title, "cardTitle"))
            card_layout.addWidget(label(description, "muted"))
            card_layout.addStretch()
            cards.addWidget(card, 1)
        layout.addLayout(cards)
        layout.addStretch()
        return page

    def show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        if index == 2:
            self.open_task_two()

    def _task_two_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(label("Task 2 - Tank Battle", "pageTitle"))
        self.task_two_layout = layout
        return page

    def open_task_two(self) -> None:
        if self.task_two is not None:
            self.task_two.setFocus()
            return
        if importlib.util.find_spec("task_2") is None:
            QMessageBox.information(
                self,
                "Task 2 chưa sẵn sàng",
                "Launcher đang chờ entry point `python -m task_2`.",
            )
            return
        if importlib.util.find_spec("pygame") is None:
            QMessageBox.warning(
                self,
                "Thiếu Pygame",
                "Cài dependency bằng lệnh: python -m pip install -r requirements.txt",
            )
            return
        try:
            from task_2.qt_widget import TankBattleWidget
            widget = TankBattleWidget()
            widget.start()
        except Exception as exc:
            QMessageBox.warning(self, "Không thể mở Task 2", str(exc))
            return
        self.task_two = widget
        self.task_two_layout.addWidget(widget, 1)

    def closeEvent(self, event) -> None:
        if self.task_two is not None:
            self.task_two.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    theme = Path(__file__).resolve().parent / "ui" / "themes.qss"
    if theme.is_file():
        app.setStyleSheet(theme.read_text(encoding="utf-8"))
    window = LauncherWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
