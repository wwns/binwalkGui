"""Testy konwertera ANSI, integracji z binwalk CLI oraz startu UI PyQt6."""

from __future__ import annotations

import gzip
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from binwalk_gui.ansi import ansi_to_html, strip_ansi
from binwalk_gui.command_builder import build_command, detect_binwalk_executables
from binwalk_gui.models import BinwalkOptions


class TestAnsiAndIntegration(unittest.TestCase):
    def test_ansi_to_html_colors_and_escaping(self) -> None:
        raw = "\x1b[31m<diff>\x1b[0m \x1b[1;32mOK\x1b[0m\nnext"
        rendered = ansi_to_html(raw)
        self.assertIn("&lt;diff&gt;", rendered)
        self.assertIn("#ff6b6b", rendered)
        self.assertIn("#51cf66", rendered)
        self.assertIn("font-weight:bold", rendered)
        self.assertIn("<br>", rendered)
        self.assertEqual(strip_ansi(raw), "<diff> OK\nnext")

    def test_real_binwalk_extract_on_synthetic_bin(self) -> None:
        binwalk_exe = detect_binwalk_executables()[0]
        payload_text = b"Hello from synthetic firmware payload!\n" * 4
        gz_data = gzip.compress(payload_text)

        with tempfile.TemporaryDirectory() as tmpdir:
            bin_path = Path(tmpdir) / "sample_fw.bin"
            out_dir = Path(tmpdir) / "out"
            out_dir.mkdir()
            # Padding + osadzony strumień gzip
            bin_path.write_bytes(b"\xff" * 256 + gz_data + b"\x00" * 64)

            opts = BinwalkOptions(
                binwalk_executable=binwalk_exe,
                extract=True,
                directory=str(out_dir),
                target_files=[str(bin_path)],
            )
            argv = build_command(opts)
            proc = subprocess.run(
                argv,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            self.assertIn("gzip compressed data", proc.stdout.lower())

            extracted_dir = out_dir / "_sample_fw.bin.extracted"
            self.assertTrue(extracted_dir.is_dir())
            extracted_files = list(extracted_dir.rglob("*"))
            self.assertTrue(any(f.is_file() for f in extracted_files))

    def test_headless_pyqt_main_window(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        win = MainWindow()
        win.show()
        win._preset_combo.setCurrentText("Głębokie rozpakowanie (-e -M)")
        preview = win._cmd_preview.text()
        self.assertIn("-e", preview)
        self.assertIn("-M", preview)

        win._option_tabs._search.setText("matryoshka")
        self.assertFalse(win._option_tabs._bindings["matryoshka"].row_widget.isHidden())
        self.assertTrue(win._option_tabs._bindings["hexdump"].row_widget.isHidden())
        win.close()

    def test_binwalk_runner_qprocess_async(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QEventLoop, QTimer
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.runner import BinwalkRunner, RunArtifacts

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        binwalk_exe = detect_binwalk_executables()[0]
        gz_data = gzip.compress(b"Async QProcess test payload\n" * 4)

        with tempfile.TemporaryDirectory() as tmpdir:
            bin_path = Path(tmpdir) / "async_fw.bin"
            bin_path.write_bytes(b"\x00" * 128 + gz_data)

            opts = BinwalkOptions(
                binwalk_executable=binwalk_exe,
                extract=True,
                target_files=[str(bin_path)],
            )
            runner = BinwalkRunner()
            loop = QEventLoop()
            chunks: list[str] = []
            results: list[RunArtifacts] = []

            runner.stdout_received.connect(chunks.append)
            runner.finished_run.connect(lambda art: (results.append(art), loop.quit()))
            QTimer.singleShot(10000, loop.quit)

            runner.start_run(build_command(opts), working_dir=tmpdir)
            loop.exec()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].exit_code, 0)
            self.assertTrue(any("gzip" in c.lower() for c in chunks))
            self.assertTrue(
                any(d.endswith("_async_fw.bin.extracted") for d in results[0].extracted_dirs)
            )


if __name__ == "__main__":
    unittest.main()
