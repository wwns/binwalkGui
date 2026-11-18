"""Testy skórek UI (light/dark/system), adaptacyjnych kolorów ANSI oraz trwałości w QSettings."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from binwalk_gui.ansi import ANSI_FG_COLORS, ANSI_FG_COLORS_LIGHT, ansi_to_html
from binwalk_gui.themes import (
    DARK_STYLESHEET,
    DEFAULT_THEME_ID,
    LIGHT_STYLESHEET,
    SYSTEM_STYLESHEET,
    THEME_LABELS,
    THEMES,
    apply_theme,
    is_dark_theme,
    normalize_theme_id,
)


class TestThemes(unittest.TestCase):
    def test_stylesheets_and_normalize_theme_id(self) -> None:
        self.assertEqual(DEFAULT_THEME_ID, "light")
        self.assertEqual(set(THEME_LABELS), {"light", "dark", "system"})
        self.assertEqual(set(THEMES), {"light", "dark", "system"})
        self.assertIn("#f4f5f7", LIGHT_STYLESHEET)
        self.assertIn("#d97706", LIGHT_STYLESHEET)
        self.assertIn("#161922", DARK_STYLESHEET)
        self.assertIn("QTextEdit#consoleView", SYSTEM_STYLESHEET)

        self.assertEqual(normalize_theme_id("light"), "light")
        self.assertEqual(normalize_theme_id("dark"), "dark")
        self.assertEqual(normalize_theme_id("system"), "system")
        self.assertEqual(normalize_theme_id("invalid-skin"), DEFAULT_THEME_ID)
        self.assertEqual(normalize_theme_id(None), DEFAULT_THEME_ID)

    def test_ansi_to_html_light_and_dark_palettes(self) -> None:
        sample = "\x1b[31mERR\x1b[0m \x1b[32mOK\x1b[0m \x1b[34mINFO\x1b[0m"
        dark_html = ansi_to_html(sample)
        light_html = ansi_to_html(sample, dark=False)

        self.assertEqual(dark_html, ansi_to_html(sample, dark=True))
        self.assertIn(ANSI_FG_COLORS[31], dark_html)
        self.assertIn(ANSI_FG_COLORS[32], dark_html)
        self.assertIn(ANSI_FG_COLORS[34], dark_html)

        self.assertIn(ANSI_FG_COLORS_LIGHT[31], light_html)
        self.assertIn(ANSI_FG_COLORS_LIGHT[32], light_html)
        self.assertIn(ANSI_FG_COLORS_LIGHT[34], light_html)
        self.assertNotIn(ANSI_FG_COLORS[31], light_html)

    def test_mainwindow_default_light_live_switching_and_qsettings_persistence(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.extractors_dialog import ExtractorCheckDialog
        from binwalk_gui.ui.main_window import DARK_STYLESHEET as MW_DARK_STYLESHEET
        from binwalk_gui.ui.main_window import MainWindow

        self.assertEqual(MW_DARK_STYLESHEET, DARK_STYLESHEET)

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            ini_path = tmp / "theme_settings.ini"
            presets_path = tmp / "presets.json"

            s1 = QSettings(str(ini_path), QSettings.Format.IniFormat)
            win1 = MainWindow(settings=s1, presets_path=presets_path)
            win1.show()

            # Domyślnie aktywna skórka "light"
            self.assertEqual(win1._theme_id, "light")
            self.assertEqual(win1._theme_combo.currentData(), "light")
            self.assertTrue(win1._theme_actions["light"].isChecked())
            self.assertFalse(win1._results._dark_mode)
            self.assertEqual(win1._results.banner_color("info"), "#1864ab")
            self.assertEqual(app.styleSheet(), LIGHT_STYLESHEET)

            # Dialog ekstraktorów w skórce jasnej
            dlg_light = ExtractorCheckDialog(win1, path_env=str(tmp))
            self.assertFalse(is_dark_theme(dlg_light))
            dlg_light.close()

            # Przełączenie na żywo przez QComboBox na "dark"
            dark_idx = win1._theme_combo.findData("dark")
            self.assertGreaterEqual(dark_idx, 0)
            win1._theme_combo.setCurrentIndex(dark_idx)

            self.assertEqual(win1._theme_id, "dark")
            self.assertTrue(win1._theme_actions["dark"].isChecked())
            self.assertTrue(win1._results._dark_mode)
            self.assertEqual(win1._results.banner_color("info"), "#74c0fc")
            self.assertEqual(app.styleSheet(), DARK_STYLESHEET)

            # Sprawdzenie adaptacyjnego koloru stderr/ANSI po przełączeniu
            win1._results.append_output("plain error\n", is_stderr=True)
            self.assertIn("#ff8787", win1._results._console.toHtml())

            # Dialog ekstraktorów w skórce ciemnej
            dlg_dark = ExtractorCheckDialog(win1, path_env=str(tmp))
            self.assertTrue(is_dark_theme(dlg_dark))
            dlg_dark.close()

            # Przełączenie na "system" przez akcję menu i z powrotem na "dark"
            win1._theme_actions["system"].trigger()
            self.assertEqual(win1._theme_id, "system")
            self.assertEqual(win1._theme_combo.currentData(), "system")
            self.assertEqual(app.styleSheet(), SYSTEM_STYLESHEET)

            win1.set_theme("dark")
            win1.close()

            # Weryfikacja trwałości ui/theme w QSettings
            s2 = QSettings(str(ini_path), QSettings.Format.IniFormat)
            self.assertEqual(s2.value("ui/theme"), "dark")

            win2 = MainWindow(settings=s2, presets_path=presets_path)
            win2.show()
            self.assertEqual(win2._theme_id, "dark")
            self.assertEqual(win2._theme_combo.currentData(), "dark")
            self.assertTrue(win2._results._dark_mode)
            self.assertEqual(app.styleSheet(), DARK_STYLESHEET)

            # Przywrócenie skórki domyślnej w QApplication na koniec testu
            apply_theme("light", win2)
            win2.close()


if __name__ == "__main__":
    unittest.main()
