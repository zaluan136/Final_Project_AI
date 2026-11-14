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
            self.assertEqual(widget.frame.size().width(), 1200)
            self.assertEqual(widget.game_pos(QPointF(300, 300)), (600, 410))
            self.assertEqual(widget.game_pos(QPointF(300, 10)), (-1, -1))
            widget.resize(1200, 820)
            self.app.processEvents()
            widget.update_game()
            rect = widget.game.field_rects["turns"]
            QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(*rect.center))
            self.assertEqual(widget.game.active_field, "turns")
            QTest.keyClicks(widget, "12")
            self.assertEqual(widget.game.fields["turns"], "12")
        finally:
            widget.stop()
            widget.close()
        self.assertFalse(widget.timer.isActive())


if __name__ == "__main__":
    unittest.main()
