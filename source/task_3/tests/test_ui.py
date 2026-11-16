import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget

from task_3 import KakuroWidget
from task_3.boards import EXAMPLE, COMPLEX_TEST
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
        widget.speed.setValue(4)
        widget.run_button.click()
        for _ in range(40):
            if widget.board_view.current_event is not None:
                break
            QTest.qWait(50)
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
        self.assertIs(widget.solver.csp.board, COMPLEX_TEST)
        self.assertIsNone(widget.board_view.current_event)
        self.assertEqual(widget.solver.assignment, {})
        widget.step_button.click()
        widget.reset_button.click()
        self.assertIsNone(widget.board_view.current_event)
        self.assertEqual(widget.log.toPlainText(), "")

    def test_board_shows_domains_only_after_search_starts(self):
        widget = self.widget
        initial = widget.board_view.grab().toImage()
        widget.step()
        self.assertNotEqual(widget.board_view.grab().toImage(), initial)
        widget.reset()
        self.assertEqual(widget.board_view.grab().toImage(), initial)
        widget.start()
        self.assertIsNotNone(widget.board_view.current_event)
        self.assertNotEqual(widget.board_view.grab().toImage(), initial)

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
        self.assertIs(embedded.solver.csp.board, EXAMPLE)
        self.assertEqual(embedded.styleSheet(), "")
        parent.deleteLater()

    def test_close_stops_timer(self):
        self.widget.start()
        self.widget.close()
        self.assertFalse(self.widget.timer.isActive())

    def test_large_board_visualizes_pruning_and_backtracking(self):
        widget = self.widget
        widget.board_picker.setCurrentIndex(1)
        seen = set()
        for _ in range(10000):
            widget.advance()
            seen.add(widget.board_view.current_event.kind)
            if widget.finished:
                break
        self.assertTrue(widget.finished)
        self.assertTrue({"try", "prune", "restore", "complete"} <= seen)
        self.assertTrue(widget.solver.csp.is_solution(widget.solver.solution))
        self.assertIn("Backtrack", widget.log.toPlainText())

    def test_progress_and_log_describe_solver_events(self):
        widget = self.widget
        self.assertEqual(widget.progress_label.text(), "Filled cells: 0 / 12")
        widget.advance()  # start
        widget.advance()  # select
        self.assertIn("Select R3C3", widget.log.toPlainText())
        widget.advance()  # try
        self.assertEqual(widget.progress_label.text(), "Filled cells: 1 / 12")
        self.assertIn("Try R3C3 = 3", widget.status.text())
        widget.advance()  # prune
        self.assertIn("Update R2C3", widget.log.toPlainText())
        self.assertIn("Active cell: R2C3", widget.run_details.text())
        widget.reset()
        self.assertEqual(widget.progress_label.text(), "Filled cells: 0 / 12")
        self.assertEqual(widget.log.toPlainText(), "")

    def test_speed_and_responsive_board(self):
        widget = self.widget
        for index, interval in enumerate((1600, 800, 400, 200, 100, 50)):
            widget.speed.setValue(index)
            self.assertEqual(widget.timer.interval(), interval)
            self.assertEqual(
                widget.speed_label.text(), f"Speed: {widget.speed_options[index][0]}"
            )
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
        theme = (Path(__file__).resolve().parents[2] / "ui" / "themes.qss").read_text(
            encoding="utf-8"
        )
        button = QPushButton("Run")
        button.setObjectName("primary")
        button.setStyleSheet(theme)
        set_button_icon(button, "play")
        button.show()
        self.app.processEvents()
        image = button.icon().pixmap(48, 48).toImage()
        colors = {
            image.pixelColor(x, y).name()
            for x in range(image.width())
            for y in range(image.height())
            if image.pixelColor(x, y).alpha() > 200
        }
        self.assertIn("#ffffff", colors)
        button.setEnabled(False)
        self.app.processEvents()
        disabled = button.icon().pixmap(48, 48, button.icon().Mode.Disabled).toImage()
        disabled_colors = {
            disabled.pixelColor(x, y).name()
            for x in range(disabled.width())
            for y in range(disabled.height())
            if disabled.pixelColor(x, y).alpha() > 200
        }
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
            colors = {
                image.pixelColor(x, y).name()
                for x in range(image.width())
                for y in range(image.height())
                if image.pixelColor(x, y).alpha() > 200
            }
            self.assertIn("#d9e1ea", colors)
        nav.close()


if __name__ == "__main__":
    unittest.main()
