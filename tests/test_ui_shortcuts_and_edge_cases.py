"""Testy skrótów klawiszowych UI, menu oraz przypadków brzegowych."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from binwalk_gui.command_builder import detect_binwalk_executables, validate_options
from binwalk_gui.models import BinwalkOptions


class TestUiShortcutsAndEdgeCases(unittest.TestCase):
    def test_validate_help_without_files_and_directory_edge_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            regular_file = Path(tmpdir) / "not_a_dir.bin"
            regular_file.write_bytes(b"\x00")
            nonexistent_dir = Path(tmpdir) / "nested" / "out_dir"

            help_opts = BinwalkOptions(show_help=True, target_files=[])
            errors, warnings = validate_options(help_opts)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

            file_as_dir_opts = BinwalkOptions(
                target_files=[str(regular_file)],
                directory=str(regular_file),
            )
            errors_file_dir, _ = validate_options(file_as_dir_opts)
            self.assertTrue(any("-C" in err for err in errors_file_dir))

            missing_dir_opts = BinwalkOptions(
                target_files=[str(regular_file)],
                extract=True,
                directory=str(nonexistent_dir),
            )
            errors_missing, _ = validate_options(missing_dir_opts)
            self.assertEqual(errors_missing, [])

    def test_menu_shortcuts_results_tabs_and_missing_dir_bar(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        win = MainWindow()
        win.show()

        # Weryfikacja skrótów w pasku menu
        shortcuts = {
            seq.toString()
            for action in win.menuBar().actions()
            if action.menu() is not None
            for sub in action.menu().actions()
            for seq in sub.shortcuts()
        }
        for expected in ("Ctrl+O", "F5", "F6", "Esc", "Ctrl+L", "Ctrl+S", "Ctrl+F", "Ctrl+R", "F1", "Ctrl+1", "Ctrl+2", "Ctrl+3"):
            self.assertIn(expected, shortcuts)

        # Przełączanie zakładek wyników i czyszczenie konsoli
        win._results.append_output("test output\n")
        self.assertIn("test output", win._results._console.toPlainText())
        win._results.show_files_tab()
        self.assertEqual(win._results._tabs.currentIndex(), 1)
        win._results.show_entropy_tab()
        self.assertEqual(win._results._tabs.currentIndex(), 2)
        win._results.show_console_tab()
        self.assertEqual(win._results._tabs.currentIndex(), 0)
        win._results.clear_console()
        self.assertEqual(win._results._console.toPlainText(), "")

        # Kopiowanie komendy i reset opcji z presetem
        win._preset_combo.setCurrentText("Skan sygnatur (-B)")
        win._copy_command()
        self.assertEqual(win._status_label.text(), "Skopiowano komendę")
        self.assertEqual(app.clipboard().text(), win._cmd_preview.text())

        win._reset_options()
        self.assertEqual(win._preset_combo.currentIndex(), 0)
        self.assertFalse(win._options.signature)

        # Wyszukiwanie i clear_search
        win._option_tabs._search.setText("matryoshka")
        self.assertTrue(win._option_tabs._bindings["hexdump"].row_widget.isHidden())
        win._option_tabs.clear_search()
        self.assertFalse(win._option_tabs._bindings["hexdump"].row_widget.isHidden())

        # Graceful display nieistniejącego katalogu -C w ResultsViewWidget
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing_out"
            win._results.set_extract_directory(str(missing))
            self.assertFalse(win._results._missing_dir_bar.isHidden())
            self.assertTrue(win._results._tree.isHidden())
            win._results._create_current_extract_dir()
            self.assertTrue(missing.is_dir())
            self.assertTrue(win._results._missing_dir_bar.isHidden())
            self.assertFalse(win._results._tree.isHidden())

        win.close()

    def test_file_list_button_states_and_cli_help_run(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QEventLoop, QTimer
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        win = MainWindow()
        win.show()

        fl = win._file_list
        self.assertFalse(fl._up_btn.isEnabled())
        self.assertFalse(fl._down_btn.isEnabled())
        self.assertFalse(fl._remove_btn.isEnabled())
        self.assertFalse(fl._clear_btn.isEnabled())

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "a.bin"
            f2 = Path(tmpdir) / "b.bin"
            f1.write_bytes(b"A")
            f2.write_bytes(b"B")
            fl.add_files([str(f1), str(f2)])
            self.assertTrue(fl._clear_btn.isEnabled())
            fl._list.setCurrentRow(0)
            self.assertFalse(fl._up_btn.isEnabled())
            self.assertTrue(fl._down_btn.isEnabled())
            self.assertTrue(fl._remove_btn.isEnabled())
            fl._remove_selected()
            self.assertEqual(len(fl.files()), 1)

            # Auto-tworzenie nieistniejącego katalogu -C przy uruchamianiu -e oraz binwalk -h bez plików
            win._exe_combo.setCurrentText(detect_binwalk_executables()[0])
            loop = QEventLoop()
            win._runner.finished_run.connect(lambda _art: loop.quit())
            QTimer.singleShot(10000, loop.quit)
            win._show_cli_help()
            loop.exec()
            self.assertFalse(win._options.show_help)
            self.assertIn("binwalk", win._results._console.toPlainText().lower())

        win.close()


if __name__ == "__main__":
    unittest.main()
