from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ui import set_button_icon
from task_3 import KakuroWidget
from task_2.qt_embed import PygameHost


def label(text: str, object_name: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setWordWrap(True)
    if object_name:
        widget.setObjectName(object_name)
    return widget


def card(title: str, description: str, icon: str, action, callback) -> QFrame:
    frame = QFrame()
    frame.setObjectName("launchCard")
    frame.setMinimumHeight(250)
    box = QVBoxLayout(frame)
    box.setContentsMargins(22, 22, 22, 22)
    box.setSpacing(12)
    box.addWidget(label(icon, "launchCardIcon"))
    box.addWidget(label(title, "launchCardTitle"))
    box.addWidget(label(description, "launchMuted"))
    box.addStretch()
    button = QPushButton(action)
    button.setObjectName("launchCardButton")
    button.clicked.connect(callback)
    box.addWidget(button, 0)
    return frame


def task_one_page() -> QWidget:
    try:
        from task_1 import NQueensPage
        return NQueensPage(embedded=True)
    except (ImportError, ModuleNotFoundError) as exc:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(label("Task 1 · N-Queens", "launchPageTitle"))
        layout.addWidget(label(f"Không thể tải giao diện: {exc}", "launchMuted"))
        layout.addStretch()
        return page


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Project · Final Project")
        self.resize(1540, 940)
        self.setMinimumSize(1480, 880)

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
        navigation.setContentsMargins(20, 26, 20, 22)
        navigation.setSpacing(9)
        navigation.addWidget(label("AI LAB", "launchBrand"))
        navigation.addWidget(label("FINAL PROJECT  /  GROUP 9", "launchEyebrow"))
        navigation.addSpacing(22)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._home_page())
        self.pages.addWidget(task_one_page())
        self.pages.addWidget(self._tank_page())
        self.pages.addWidget(KakuroWidget())

        self.nav_buttons: list[QPushButton] = []
        entries = (
            ("Tổng quan", "home", 0),
            ("Task 1 · N-Queens", "queen", 1),
            ("Task 2 · Tank Battle", "game", 2),
            ("Task 3 · Kakuro", "grid", 3),
        )
        for title, icon, index in entries:
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            set_button_icon(button, icon)
            button.clicked.connect(lambda _, i=index: self.show_page(i))
            navigation.addWidget(button)
            self.nav_buttons.append(button)
        navigation.addStretch()
        navigation.addWidget(label("524H0098  ·  524H0101  ·  524H0109", "launchMuted"))
        shell.addWidget(sidebar)
        shell.addWidget(self.pages, 1)
        self.show_page(0)

    def _home_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("launchHome")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(42, 36, 42, 34)
        layout.setSpacing(22)

        hero = QFrame()
        hero.setObjectName("launchHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(30, 26, 30, 28)
        hero_layout.setSpacing(8)
        hero_layout.addWidget(label("FINAL PROJECT  ·  ARTIFICIAL INTELLIGENCE", "launchHeroEyebrow"))
        hero_layout.addWidget(label("Một dự án. Ba bài toán AI.", "launchHeroTitle"))
        hero_layout.addWidget(label(
            "Khám phá cách tìm kiếm, chiến lược đối kháng và ràng buộc giúp máy tính giải quyết vấn đề.",
            "launchHeroCopy",
        ))
        layout.addWidget(hero)

        section = QHBoxLayout()
        section.addWidget(label("Các bài toán", "launchSection"))
        section.addStretch()
        section.addWidget(label("CHỌN MỘT BÀI ĐỂ BẮT ĐẦU", "launchEyebrow"))
        layout.addLayout(section)
        row = QHBoxLayout()
        row.setSpacing(18)
        for title, description, icon, action, callback in (
            ("N-Queens", "Đặt N quân hậu lên bàn cờ mà không để chúng ăn nhau.", "01", "Mở bài toán", lambda: self.show_page(1)),
            ("Tank Battle", "Lập chiến thuật cho xe tăng trong trận đấu mô phỏng.", "02", "Mở đấu trường", self.open_task_two),
            ("Kakuro", "Giải ô chữ số bằng các ràng buộc tổng và chữ số khác nhau.", "03", "Mở bài toán", lambda: self.show_page(3)),
        ):
            row.addWidget(card(title, description, icon, action, callback), 1)
        layout.addLayout(row)
        footer = QFrame()
        footer.setObjectName("launchFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 13, 18, 13)
        footer_layout.addWidget(label("AI LAB", "launchFooterTag"))
        footer_layout.addWidget(label("N-Queens  ·  Tank Battle  ·  Kakuro", "launchMuted"))
        footer_layout.addStretch()
        footer_layout.addWidget(label("GROUP 9", "launchEyebrow"))
        layout.addWidget(footer)
        layout.addStretch()
        return page

    def _tank_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("launchTankPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tank_host = PygameHost(page)
        self.tank_host.failed.connect(self._tank_embed_failed)
        layout.addWidget(self.tank_host)
        return page

    def show_page(self, index: int) -> None:
        if self.pages.currentIndex() == 2 and index != 2:
            self.tank_host.stop()
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        if index == 2:
            self.tank_host.start()

    def open_task_two(self) -> None:
        self.show_page(2)

    def _tank_embed_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Tank Battle", message)

    def closeEvent(self, event) -> None:
        if hasattr(self, "tank_host"):
            self.tank_host.stop()
        super().closeEvent(event)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet("""
        QFrame#sidebar { background: #142a32; border: 0; }
        QWidget#launchHome, QWidget#launchTankPage { background: #f4f7f6; }
        QLabel#launchBrand { color: #f5faf8; font-size: 23px; font-weight: 750; }
        QLabel#launchEyebrow { color: #71847f; font-size: 9px; font-weight: 700; }
        QLabel#launchHeroEyebrow { color: #b8dfd2; font-size: 10px; font-weight: 700; }
        QLabel#launchHeroTitle { color: #ffffff; font-size: 29px; font-weight: 750; }
        QLabel#launchHeroCopy { color: #d3e5df; font-size: 14px; }
        QLabel#launchPageTitle { color: #182532; font-size: 30px; font-weight: 700; }
        QLabel#launchCardIcon { color: #168568; background: #e5f2ed; border-radius: 16px; padding: 7px; font-size: 11px; font-weight: 750; }
        QLabel#launchCardTitle, QLabel#launchSection { color: #213a36; font-size: 18px; font-weight: 700; }
        QLabel#launchMuted { color: #73837f; font-size: 13px; }
        QLabel#launchFooterTag { color: #17785f; font-size: 11px; font-weight: 750; }
        QFrame#launchHero { background: #176c58; border: 0; border-radius: 16px; }
        QFrame#launchCard, QFrame#launchPanel { background: #ffffff; border: 1px solid #e1eae6; border-radius: 14px; }
        QFrame#launchFooter { background: #eaf2ef; border: 0; border-radius: 9px; }
        QPushButton#launchCardButton { color: #ffffff; background: #17785f; border: 0; border-radius: 7px; padding: 11px 13px; text-align: left; font-weight: 650; }
        QPushButton#launchCardButton:hover { background: #105e49; }
        QPushButton#nav { color: #c0d0ca; text-align: left; border: 0; border-radius: 8px; padding: 12px 13px; }
        QPushButton#nav:hover { background: #213e44; color: white; }
        QPushButton#nav:checked { background: #20775f; color: white; font-weight: 650; }
        QPushButton#tankLaunchButton { background: #17785f; color: white; border: 0; border-radius: 7px; padding: 10px 16px; font-weight: 650; }
        QPushButton#tankLaunchButton:hover { background: #105e49; }
    """)
    window = LauncherWindow()
    app.aboutToQuit.connect(window.tank_host.stop)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
