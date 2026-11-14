import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from task_2.qt_widget import TankBattleWidget


class EmbeddedGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_scaling_mouse_and_stop(self):
        widget = TankBattleWidget()
        widget.resize(600, 600)
        widget.show()
        widget.start()
        try:
            widget.update_game()
            assert widget.frame is not None
            assert widget.game is not None
            self.assertEqual(widget.frame.size().width(), 600)
            self.assertEqual(widget.game_pos(QPointF(300, 300)), (600, 410))
            self.assertEqual(widget.game_pos(QPointF(300, 10)), (-1, -1))
            rect = widget.game.field_rects["turns"]
            target = widget.target_rect()
            point = QPoint(
                round(target.x() + rect.centerx * target.width() / 1200),
                round(target.y() + rect.centery * target.height() / 820),
            )
            QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=point)
            self.assertEqual(widget.game.active_field, "turns")
            widget.resize(1200, 820)
            self.app.processEvents()
            widget.update_game()
            assert widget.frame is not None
            self.assertEqual(widget.frame.width(), 1200)
            rect = widget.game.field_rects["turns"]
            QTest.mouseClick(
                widget, Qt.MouseButton.LeftButton, pos=QPoint(*rect.center)
            )
            self.assertEqual(widget.game.active_field, "turns")
            QTest.keyClicks(widget, "12")
            self.assertEqual(widget.game.fields["turns"], "12")
        finally:
            widget.stop()
            widget.close()
        self.assertFalse(widget.timer.isActive())

    def test_restart_same_widget(self):
        widget = TankBattleWidget()
        widget.resize(900, 650)
        widget.start()
        try:
            widget.update_game()
            widget.stop()
            widget.start()
            widget.update_game()
            assert widget.frame is not None
            self.assertEqual(widget.frame.size().width(), 900)
        finally:
            widget.stop()
            widget.close()


if __name__ == "__main__":
    unittest.main()
