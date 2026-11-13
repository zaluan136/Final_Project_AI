import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget

from task_3 import KakuroWidget
from task_3.boards import DEMO, TASK


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        if not QFontDatabase.families() and os.name == "nt":
            QFontDatabase.addApplicationFont("C:/Windows/Fonts/arial.ttf")

    def setUp(self):
        self.widget = KakuroWidget()
        self.widget.resize(1120, 800)
        self.widget.show()
        self.app.processEvents()

    def tearDown(self):
        self.widget.reset()
        self.widget.close()
        self.widget.deleteLater()
        self.app.processEvents()

    def test_pause_step_reset_and_board_switch(self):
        widget = self.widget
        widget.speed.setValue(100)
        widget.run_button.click()
        QTest.qWait(35)
        self.assertTrue(widget.timer.isActive())
        widget.pause_button.click()
        event = widget.board_view.current_event
        self.assertIsNotNone(event)
        QTest.qWait(25)
        self.assertIs(widget.board_view.current_event, event)
        widget.step_button.click()
        self.assertIsNot(widget.board_view.current_event, event)
        self.assertFalse(widget.timer.isActive())
        widget.run_button.click()
        widget.board_picker.setCurrentIndex(1)
        self.assertFalse(widget.timer.isActive())
        self.assertIs(widget.solver.csp.board, TASK)
        self.assertIsNone(widget.board_view.current_event)
        self.assertEqual(widget.solver.assignment, {})
        widget.step_button.click()
        widget.reset_button.click()
        self.assertIsNone(widget.board_view.current_event)
        self.assertEqual(widget.log.toPlainText(), "")

    def test_completion_and_embedded_widget(self):
        widget = self.widget
        for _ in range(500):
            widget.advance()
            if widget.finished:
                break
        self.assertTrue(widget.finished)
        self.assertTrue(widget.solver.csp.is_solution(widget.solver.solution))
        self.assertFalse(widget.run_button.isEnabled())
        self.assertFalse(widget.step_button.isEnabled())
        self.assertFalse(widget.timer.isActive())
        self.assertFalse(widget.grab().isNull())
        parent = QWidget()
        embedded = KakuroWidget(parent=parent)
        self.assertIs(embedded.parent(), parent)
        self.assertIs(embedded.solver.csp.board, DEMO)
        self.assertEqual(embedded.styleSheet(), "")
        parent.deleteLater()

    def test_close_stops_timer(self):
        self.widget.start()
        self.widget.close()
        self.assertFalse(self.widget.timer.isActive())


if __name__ == "__main__":
    unittest.main()
