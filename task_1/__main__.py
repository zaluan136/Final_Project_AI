"""Run Task 1 as a standalone PySide6 application."""

import sys

from PySide6.QtWidgets import QApplication

from .app import MainWindow, STYLES


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLES)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
