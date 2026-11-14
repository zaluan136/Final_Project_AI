import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget

from task_3 import KakuroWidget
from task_3.boards import DEMO, TASK
from ui import set_button_icon
from PySide6.QtWidgets import QPushButton


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
        widget.speed.setCurrentIndex(3)
        widget.run_button.click()
        QTest.qWait(120)
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

    def test_speed_and_responsive_board(self):
        widget = self.widget
        for index, interval in enumerate((400, 200, 100, 50)):
            widget.speed.setCurrentIndex(index)
            self.assertEqual(widget.timer.interval(), interval)
        demo_size, x, y = widget.board_view.board_geometry()
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        widget.board_picker.setCurrentIndex(1)
        task_size, x, y = widget.board_view.board_geometry()
        self.assertGreater(demo_size, task_size)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        widget.splitter.setSizes([400, 600])
        self.app.processEvents()
        self.assertGreater(widget.splitter.sizes()[1], widget.splitter.sizes()[0])

    def test_icons_follow_themed_button_text(self):
        theme = (Path(__file__).resolve().parents[2] / "ui" / "themes.qss").read_text(encoding="utf-8")
        button = QPushButton("Run")
        button.setObjectName("primary")
        button.setStyleSheet(theme)
        set_button_icon(button, "play")
        button.show()
        self.app.processEvents()
        image = button.icon().pixmap(48, 48).toImage()
        colors = {image.pixelColor(x, y).name() for x in range(image.width())
                  for y in range(image.height()) if image.pixelColor(x, y).alpha() > 200}
        self.assertIn("#ffffff", colors)
        button.setEnabled(False)
        self.app.processEvents()
        disabled = button.icon().pixmap(48, 48, button.icon().Mode.Disabled).toImage()
        disabled_colors = {disabled.pixelColor(x, y).name() for x in range(disabled.width())
                           for y in range(disabled.height()) if disabled.pixelColor(x, y).alpha() > 200}
        self.assertIn("#ffffff", disabled_colors)
        button.close()

        nav = QPushButton("Task 2")
        nav.setObjectName("nav")
        nav.setCheckable(True)
        nav.setStyleSheet(theme)
        set_button_icon(nav, "game")
        nav.show()
        for checked in (False, True):
            nav.setChecked(checked)
            self.app.processEvents()
            image = nav.icon().pixmap(48, 48).toImage()
            colors = {image.pixelColor(x, y).name() for x in range(image.width())
                      for y in range(image.height()) if image.pixelColor(x, y).alpha() > 200}
            self.assertIn("#d9e1ea", colors)
        nav.close()


if __name__ == "__main__":
    unittest.main()
