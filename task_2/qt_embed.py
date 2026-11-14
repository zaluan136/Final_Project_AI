"""Qt host for the existing Pygame game window (Windows/SDL_WINDOWID)."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PygameHost(QWidget):
    """Run the Pygame frame loop inside a native Qt child widget."""

    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tankGameHost")
        self.setMinimumSize(1200, 820)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.game = None
        self._pygame = None
        self._old_window_id = os.environ.get("SDL_WINDOWID")
        self._message = QLabel("Đang khởi tạo Tank Battle…", self)
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._message)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._frame)

    def start(self):
        if self.game is not None:
            self.timer.start()
            return
        if sys.platform != "win32":
            self._fail("Nhúng cửa sổ Pygame hiện được cấu hình cho Windows.")
            return
        try:
            import pygame
            self._pygame = pygame

            # SDL reads this handle when its video driver initializes.
            os.environ["SDL_WINDOWID"] = str(int(self.winId()))
            pygame.display.init()
            pygame.font.init()
            screen = pygame.display.set_mode((1200, 820))
            pygame.display.set_caption("Tank Battle | AI Project")
            from task_2.play import Playground

            self.game = Playground(screen)
            self._message.hide()
            self.timer.start()
            self.setFocus(Qt.FocusReason.OtherFocusReason)
        except Exception as exc:
            self._fail(f"Không thể nhúng cửa sổ Pygame: {type(exc).__name__}: {exc}")

    def _frame(self):
        if self.game is None:
            return
        try:
            self.game.frame()
            if not self.game.running:
                self.stop()
                self._message.setText("Trận đấu đã đóng. Chọn Tank Battle để mở lại.")
                self._message.show()
        except Exception as exc:
            self._fail(f"Lỗi khi chạy game: {type(exc).__name__}: {exc}")

    def _fail(self, message: str):
        self.timer.stop()
        self._message.setText(message)
        self._message.show()
        self.failed.emit(message)
        self.stop()

    def stop(self):
        self.timer.stop()
        game, self.game = self.game, None
        if game is not None:
            game.close()
        if self._pygame is not None:
            self._pygame.display.quit()
            self._pygame.font.quit()
            self._pygame = None
        if self._old_window_id is None:
            os.environ.pop("SDL_WINDOWID", None)
        else:
            os.environ["SDL_WINDOWID"] = self._old_window_id

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
