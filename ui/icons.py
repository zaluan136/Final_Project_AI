"""SVG icon registry shared by all Qt surfaces."""

from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QObject, QRectF, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QStyleOptionButton

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
    svg = svg.replace("currentColor", color).replace("#F8FAFC", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(48, 48)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(4, 4, 40, 40))
    painter.end()
    result = QIcon()
    for mode in (QIcon.Mode.Normal, QIcon.Mode.Disabled, QIcon.Mode.Active, QIcon.Mode.Selected):
        result.addPixmap(pixmap, mode)
    return result


class _ButtonIconUpdater(QObject):
    """Keep the SVG in step with the widget's current system palette."""

    def __init__(self, button, name: str):
        super().__init__(button)
        self.button = button
        self.name = name
        self._color = None
        button.installEventFilter(self)
        self.update_icon()

    def update_icon(self):
        option = QStyleOptionButton()
        self.button.initStyleOption(option)
        group = option.palette.currentColorGroup()
        color = option.palette.color(group, QPalette.ColorRole.ButtonText).name()
        if color != self._color:
            self._color = color
            self.button.setIcon(icon(self.name, color))

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.PaletteChange, QEvent.Type.EnabledChange,
                            QEvent.Type.StyleChange, QEvent.Type.Paint):
            self.update_icon()
        return False


def set_button_icon(button, name: str, size: int = 20) -> None:
    # Retain the filter with the button so it follows later palette changes.
    if hasattr(button, "_svg_icon_updater"):
        button.removeEventFilter(button._svg_icon_updater)
        button._svg_icon_updater.deleteLater()
    button._svg_icon_updater = _ButtonIconUpdater(button, name)
    button.setIconSize(QSize(size, size))
