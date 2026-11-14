import sys

from PySide6.QtWidgets import QApplication
from .ui import KakuroWidget


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    widget = KakuroWidget()
    widget.resize(1120, 800)
    widget.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
