import os
from typing import cast

import pygame
from PySide6.QtCore import QRectF, QTimer, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from .play import Playground
from .scaled_canvas import ScaledCanvas


class TankBattleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(1, 1)
        self.game: Playground | None = None
        self.frame: QImage | None = None
        self.canvas_size = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)

    def start(self):
        if self.game is not None:
            return
        previous_driver = os.environ.get("SDL_VIDEODRIVER")
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        try:
            pygame.init()
            pygame.display.set_mode((1, 1))
        finally:
            if previous_driver is None:
                os.environ.pop("SDL_VIDEODRIVER", None)
            else:
                os.environ["SDL_VIDEODRIVER"] = previous_driver
        self.game = Playground(pygame.Surface((1200, 820)))
        self.game.embedded_mouse_pos = (-1, -1)
        self.timer.start(33)
        self.setFocus()

    def stop(self):
        self.timer.stop()
        if self.game is not None:
            self.game.close()
            self.game = None
            pygame.quit()
        self.canvas_size = None
        self.frame = None

    def update_game(self):
        if self.game is None:
            return
        pygame.event.pump()
        self.game.poll_worker()
        self.game.notify(self.game.tick_match)
        target = self.target_rect()
        ratio = self.devicePixelRatioF()
        size = (
            max(1, round(target.width() * ratio)),
            max(1, round(target.height() * ratio)),
        )
        if size != self.canvas_size:
            self.game.resize_canvas(size)
            self.canvas_size = size
        self.game.draw()
        canvas = cast(object, self.game.screen)
        if not isinstance(canvas, ScaledCanvas):
            raise RuntimeError("Embedded game requires a scaled canvas")
        pixels = pygame.image.tobytes(canvas.surface, "RGB")
        self.frame = QImage(
            pixels, size[0], size[1], size[0] * 3, QImage.Format.Format_RGB888
        ).copy()
        self.update()

    def target_rect(self):
        scale = min(self.width() / 1200, self.height() / 820)
        width, height = 1200 * scale, 820 * scale
        return QRectF(
            (self.width() - width) / 2, (self.height() - height) / 2, width, height
        )

    def game_pos(self, position):
        target = self.target_rect()
        if not target.contains(position) or target.width() <= 0 or target.height() <= 0:
            return (-1, -1)
        return (
            int((position.x() - target.x()) * 1200 / target.width()),
            int((position.y() - target.y()) * 820 / target.height()),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.frame is not None:
            painter.drawImage(self.target_rect(), self.frame, QRectF(self.frame.rect()))

    def mouseMoveEvent(self, event):
        if self.game:
            self.game.embedded_mouse_pos = self.game_pos(event.position())

    def leaveEvent(self, event):
        if self.game:
            self.game.embedded_mouse_pos = (-1, -1)

    def mousePressEvent(self, event):
        if self.game is None:
            return
        self.setFocus()
        pos = self.game_pos(event.position())
        self.game.embedded_mouse_pos = pos
        button = {Qt.MouseButton.LeftButton: 1, Qt.MouseButton.RightButton: 3}.get(
            event.button()
        )
        if button and pos != (-1, -1):
            self.game.handle(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)
            )

    def keyPressEvent(self, event):
        if self.game is None:
            return
        if (
            event.key() == Qt.Key.Key_V
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and self.game.active_field == "path"
        ):
            value = QApplication.clipboard().text().replace("\x00", "").strip()
            self.game.fields["path"] = (
                "" if self.game.select_all_text else self.game.fields["path"]
            ) + value
            self.game.select_all_text = False
            return
        special = {
            Qt.Key.Key_Up: pygame.K_UP,
            Qt.Key.Key_Down: pygame.K_DOWN,
            Qt.Key.Key_Left: pygame.K_LEFT,
            Qt.Key.Key_Right: pygame.K_RIGHT,
            Qt.Key.Key_Return: pygame.K_RETURN,
            Qt.Key.Key_Enter: pygame.K_RETURN,
            Qt.Key.Key_Escape: pygame.K_ESCAPE,
            Qt.Key.Key_Backspace: pygame.K_BACKSPACE,
            Qt.Key.Key_Space: pygame.K_SPACE,
        }
        key = special.get(
            event.key(), ord(event.text().lower()) if len(event.text()) == 1 else 0
        )
        if Qt.Key.Key_A <= event.key() <= Qt.Key.Key_Z:
            key = ord("a") + event.key() - Qt.Key.Key_A
        mod = (
            pygame.KMOD_CTRL
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier
            else 0
        )
        self.game.handle(
            pygame.event.Event(pygame.KEYDOWN, key=key, unicode=event.text(), mod=mod)
        )
