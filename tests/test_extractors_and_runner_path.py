"""Testy diagnostyki zewnętrznych ekstraktorów oraz wstrzykiwania PATH w BinwalkRunner."""

from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from binwalk_gui.extractors import EXTRACTOR_SPECS, build_augmented_path, check_extractors


def _make_executable(path: Path) -> None:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class TestExtractorsAndRunnerPath(unittest.TestCase):
    def test_build_augmented_path_deduplicates_and_appends(self) -> None:
        local_bin = str(Path.home() / ".local" / "bin")
        base = os.pathsep.join(["/usr/bin", local_bin, "/usr/bin", ""])
        augmented = build_augmented_path(base)
        parts = augmented.split(os.pathsep)

        self.assertEqual(parts[0], "/usr/bin")
        self.assertEqual(parts.count(local_bin), 1)
        self.assertEqual(parts.count("/usr/local/bin"), 1)
        self.assertIn(local_bin, parts)
        self.assertIn("/usr/local/bin", parts)

    def test_check_extractors_detects_executable_and_ignores_non_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fake_jefferson = tmp / "jefferson"
            _make_executable(fake_jefferson)

            # Zwykły plik bez bitu +x nie powinien być wykryty jako dostępny
            non_exec = tmp / "unstuff"
            non_exec.write_text("not executable", encoding="utf-8")
            non_exec.chmod(0o644)

            statuses = check_extractors(path_env=str(tmp))
            self.assertEqual(len(statuses), len(EXTRACTOR_SPECS))
            by_cmd = {s.info.command: s for s in statuses}

            self.assertTrue(by_cmd["jefferson"].available)
            self.assertEqual(by_cmd["jefferson"].path, str(fake_jefferson))
            if not (Path.home() / ".local" / "bin" / "unstuff").is_file() and not Path(
                "/usr/local/bin/unstuff"
            ).is_file():
                self.assertFalse(by_cmd["unstuff"].available)
                self.assertIsNone(by_cmd["unstuff"].path)

    def test_extractor_check_dialog_offscreen_and_refresh(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.extractors_dialog import ExtractorCheckDialog

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dlg = ExtractorCheckDialog(path_env=str(tmp))
            self.assertEqual(dlg._table.rowCount(), len(EXTRACTOR_SPECS))
            self.assertEqual(dlg._table.columnCount(), 5)
            self.assertIn(f"/ {len(EXTRACTOR_SPECS)}", dlg._summary_label.text())
            self.assertFalse(dlg._copy_btn.isEnabled())
            self.assertFalse(dlg.copy_selected_hint())

            # Zaznaczenie wiersza 0 (jefferson) włącza kopiowanie instrukcji instalacji
            dlg._table.selectRow(0)
            self.assertTrue(dlg._copy_btn.isEnabled())
            self.assertTrue(dlg.copy_selected_hint())
            self.assertEqual(app.clipboard().text(), EXTRACTOR_SPECS[0].install_hint)
            self.assertIn("jefferson", dlg._feedback_label.text())

            # Dodanie fałszywego ekstraktora i odświeżenie tabeli
            fake_sasquatch = tmp / "sasquatch"
            _make_executable(fake_sasquatch)
            dlg.refresh()
            self.assertEqual(dlg._table.item(1, 0).text(), "sasquatch")
            self.assertEqual(dlg._table.item(1, 1).text(), "Dostępny")
            self.assertEqual(dlg._table.item(1, 2).text(), str(fake_sasquatch))
            dlg.close()

    def test_binwalk_runner_injects_augmented_path_into_qprocess(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QEventLoop, QTimer
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.runner import BinwalkRunner, RunArtifacts

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        runner = BinwalkRunner()
        loop = QEventLoop()
        chunks: list[str] = []
        results: list[RunArtifacts] = []

        runner.stdout_received.connect(chunks.append)
        runner.finished_run.connect(lambda art: (results.append(art), loop.quit()))
        QTimer.singleShot(5000, loop.quit)

        with tempfile.TemporaryDirectory() as tmpdir:
            runner.start_run(
                [sys.executable, "-c", "import os; print(os.environ.get('PATH', ''))"],
                working_dir=tmpdir,
            )
            loop.exec()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].exit_code, 0)
        child_path = "".join(chunks).strip().split(os.pathsep)
        self.assertIn(str(Path.home() / ".local" / "bin"), child_path)
        self.assertIn("/usr/local/bin", child_path)

    def test_mainwindow_missing_extractor_banner_and_menu_action(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            win = MainWindow(
                settings=QSettings(str(tmp / "s.ini"), QSettings.Format.IniFormat),
                presets_path=tmp / "presets.json",
            )
            win.show()

            help_actions = [
                sub.text()
                for action in win.menuBar().actions()
                if action.menu() is not None and "omoc" in action.text()
                for sub in action.menu().actions()
            ]
            self.assertIn("Sprawdź ekstraktory...", help_actions)

            win._on_run_started(str(tmp))
            win._on_runner_output("WARNING: Extractor.execute failed to ", True)
            win._on_runner_output("run external extractor 'jefferson'", True)
            self.assertTrue(win._missing_extractor_detected)
            self.assertIn("Sprawdź ekstraktory...", win._status_label.text())
            self.assertIn("Sprawdź ekstraktory...", win._results._console.toPlainText())
            win.close()


if __name__ == "__main__":
    unittest.main()
