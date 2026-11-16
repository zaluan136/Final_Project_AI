from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PySide6.QtCore import QDir
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
            "Task 1 does not provide the `task_1` package with the `NQueensPage` API. "
            "Once the module has the expected structure, the launcher will embed it here.\n\n"
            f"Details: {exc}",
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
        layout.setContentsMargins(56, 48, 56, 48)
        layout.setSpacing(12)
        layout.addWidget(label("FINAL PROJECT  /  GROUP 9", "introEyebrow"))
        layout.addWidget(
            label("Introduction to\nArtificial Intelligence", "introTitle")
        )
        layout.addWidget(
            label("503043  -  Semester 1, Academic Year 2026–2027", "introDetails")
        )
        layout.addSpacing(24)

        members = QFrame()
        members.setObjectName("card")
        members.setMaximumWidth(700)
        members_layout = QVBoxLayout(members)
        members_layout.setContentsMargins(28, 24, 28, 24)
        members_layout.setSpacing(14)
        members_layout.addWidget(label("Group 9", "introGroup"))
        members_layout.addWidget(
            label("524H0098   -   Nguyễn Hòa Khang", "introMember")
        )
        members_layout.addWidget(label("524H0109   -   Lý Gia Luân", "introMember"))
        members_layout.addWidget(
            label("524H0101   -   Nguyễn Thái Khoa", "introMember")
        )
        layout.addWidget(members)
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
                "Task 2 is not available",
                "The launcher could not find the `task_2` package.",
            )
            return
        if importlib.util.find_spec("pygame") is None:
            QMessageBox.warning(
                self,
                "Pygame is missing",
                "Install dependencies with: python -m pip install -r requirements.txt",
            )
            return
        try:
            from task_2.qt_widget import TankBattleWidget

            widget = TankBattleWidget()
            widget.start()
        except Exception as exc:
            QMessageBox.warning(self, "Could not open Task 2", str(exc))
            return
        self.task_two = widget
        self.task_two_layout.addWidget(widget, 1)

    def closeEvent(self, event) -> None:
        if self.task_two is not None:
            self.task_two.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    if not isinstance(app, QApplication):
        raise RuntimeError("Launcher requires a QApplication")
    theme = Path(__file__).resolve().parent / "ui" / "themes.qss"
    if theme.is_file():
        QDir.addSearchPath("theme", str(theme.parent))
        app.setStyleSheet(theme.read_text(encoding="utf-8"))
    window = LauncherWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
