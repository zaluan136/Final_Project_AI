"""SVG icon registry shared by all Qt surfaces."""

from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QObject, QRectF, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
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


class _ButtonIconUpdater(QObject):
    """Keep the SVG in step with the widget's current system palette."""

    def __init__(self, button, name: str):
        super().__init__(button)
        self.button = button
        self.name = name
        button.installEventFilter(self)
        self.update_icon()

    def update_icon(self):
        group = QPalette.ColorGroup.Active if self.button.isEnabled() else QPalette.ColorGroup.Disabled
        color = self.button.palette().color(group, QPalette.ColorRole.ButtonText).name()
        self.button.setIcon(icon(self.name, color))

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.EnabledChange):
            self.update_icon()
        return False


def set_button_icon(button, name: str, size: int = 20) -> None:
    # Retain the filter with the button so it follows later palette changes.
    if hasattr(button, "_svg_icon_updater"):
        button.removeEventFilter(button._svg_icon_updater)
        button._svg_icon_updater.deleteLater()
    button._svg_icon_updater = _ButtonIconUpdater(button, name)
    button.setIconSize(QSize(size, size))
