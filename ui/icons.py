"""SVG icon registry shared by all Qt surfaces."""

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"


def icon_path(name: str) -> str:
    path = _ICON_DIR / f"{name}.svg"
    if not path.is_file():
        raise KeyError(f"Unknown shared icon: {name}")
    return str(path)


def icon(name: str, color: str | None = None) -> QIcon:
    if color is None or name == "queen-board":
        return QIcon(icon_path(name))
    svg = (_ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    svg = svg.replace("#F8FAFC", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(48, 48)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(4, 4, 40, 40))
    painter.end()
    return QIcon(pixmap)


def set_button_icon(button, name: str, size: int = 20) -> None:
    color = "#FFFFFF" if button.objectName() == "primary" else "#294233"
    button.setIcon(icon(name, color))
    button.setIconSize(QSize(size, size))
