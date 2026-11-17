"""Testy trwałości QSettings oraz własnych presetów JSON (bez modyfikacji ~/.config)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from binwalk_gui.command_builder import default_binwalk_executable, detect_binwalk_executables
from binwalk_gui.models import OPTION_SPECS, PRESETS, BinwalkOptions
from binwalk_gui.presets_store import (
    apply_preset_dict,
    delete_custom_preset,
    load_custom_presets,
    options_to_preset_dict,
    save_custom_preset,
)


class TestSettingsAndCustomPresets(unittest.TestCase):
    def test_presets_store_roundtrip_all_54_flags_and_edge_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            presets_file = Path(tmpdir) / "nested" / "presets.json"

            # Brak pliku oraz uszkodzony JSON
            self.assertEqual(load_custom_presets(presets_file), {})
            presets_file.parent.mkdir(parents=True, exist_ok=True)
            presets_file.write_text("{corrupt json", encoding="utf-8")
            self.assertEqual(load_custom_presets(presets_file), {})
            presets_file.write_text('["not", "a", "dict"]', encoding="utf-8")
            self.assertEqual(load_custom_presets(presets_file), {})

            # Pełny round-trip wszystkich 54 flag OPTION_SPECS
            full_opts = BinwalkOptions(
                binwalk_executable="/usr/bin/binwalk",
                use_long_flags=True,
                target_files=["ignored_by_preset.bin"],
            )
            for spec in OPTION_SPECS:
                if spec.kind == "bool":
                    setattr(full_opts, spec.field_name, True)
                elif spec.kind in ("list", "list_file"):
                    setattr(full_opts, spec.field_name, ["v1", "v2"])
                elif spec.kind == "float":
                    setattr(full_opts, spec.field_name, "0.92")
                elif spec.kind == "int_hex":
                    setattr(full_opts, spec.field_name, "0x20")
                else:
                    setattr(full_opts, spec.field_name, "custom_val")

            saved = save_custom_preset("Pelny profil", full_opts, presets_file)
            self.assertIn("Pelny profil", saved)
            self.assertTrue(presets_file.is_file())

            # Dopisanie nieznanego pola i próby nadpisania wbudowanego presetu do pliku JSON
            raw_json = json.loads(presets_file.read_text(encoding="utf-8"))
            raw_json["Pelny profil"]["unknown_future_flag"] = True
            raw_json["Szybkie rozpakowanie (-e)"] = {"signature": True}
            presets_file.write_text(json.dumps(raw_json), encoding="utf-8")

            loaded = load_custom_presets(presets_file)
            self.assertIn("Pelny profil", loaded)
            self.assertNotIn("Szybkie rozpakowanie (-e)", loaded)
            self.assertNotIn("unknown_future_flag", loaded["Pelny profil"])

            base = BinwalkOptions(
                binwalk_executable="/custom/binwalk",
                use_long_flags=False,
                target_files=["fw.bin"],
                directory="/tmp/base_out",
            )
            applied = apply_preset_dict(base, loaded["Pelny profil"])
            self.assertEqual(applied.binwalk_executable, "/custom/binwalk")
            self.assertFalse(applied.use_long_flags)
            self.assertEqual(applied.target_files, ["fw.bin"])
            for spec in OPTION_SPECS:
                self.assertEqual(
                    getattr(applied, spec.field_name),
                    getattr(full_opts, spec.field_name),
                    msg=f"Mismatch for {spec.field_name}",
                )

            # Ochrona wbudowanych presetów i pustych nazw
            with self.assertRaises(ValueError):
                save_custom_preset("", full_opts, presets_file)
            builtin_name = next(iter(PRESETS))
            with self.assertRaises(ValueError):
                save_custom_preset(builtin_name, full_opts, presets_file)

            after_builtin_del = delete_custom_preset(builtin_name, presets_file)
            self.assertIn("Pelny profil", after_builtin_del)

            after_del = delete_custom_preset("Pelny profil", presets_file)
            self.assertEqual(after_del, {})
            self.assertEqual(options_to_preset_dict(BinwalkOptions()), {})

    def test_mainwindow_custom_presets_and_qsettings_isolation(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QApplication

        from binwalk_gui.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        self.assertIsNotNone(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            ini_path = tmp / "settings.ini"
            presets_path = tmp / "presets.json"
            extract_dir = tmp / "extract_out"
            extract_dir.mkdir()
            exe = detect_binwalk_executables()[0]

            s1 = QSettings(str(ini_path), QSettings.Format.IniFormat)
            win1 = MainWindow(settings=s1, presets_path=presets_path)
            win1.show()

            # Ustawienie opcji, zapis własnego presetu oraz ustawień okna
            win1._long_flags_cb.setChecked(True)
            win1._quick_dir.setText(str(extract_dir))
            win1._exe_combo.setCurrentText(exe)
            win1._quick_matryoshka.setChecked(True)
            win1._option_tabs._bindings["entropy"].control.setChecked(True)
            win1._splitter.setSizes([320, 480])

            self.assertFalse(win1.save_custom_preset("Szybkie rozpakowanie (-e)"))
            self.assertFalse(win1.delete_custom_preset("Szybkie rozpakowanie (-e)"))
            self.assertTrue(win1.save_custom_preset("Mój profil"))
            self.assertTrue(win1._delete_preset_btn.isEnabled())
            self.assertEqual(
                win1._preset_combo.currentText(),
                f"{MainWindow.CUSTOM_PRESET_PREFIX}Mój profil",
            )

            # Przełączenie na wbudowany preset blokuje przycisk usuwania
            win1._preset_combo.setCurrentText("Szybkie rozpakowanie (-e)")
            self.assertFalse(win1._delete_preset_btn.isEnabled())

            win1.close()

            # Ponowne otwarcie z tymi samymi plikami testowymi przywraca QSettings i własny preset
            s2 = QSettings(str(ini_path), QSettings.Format.IniFormat)
            win2 = MainWindow(settings=s2, presets_path=presets_path)
            win2.show()

            self.assertTrue(win2._options.use_long_flags)
            self.assertEqual(win2._options.directory, str(extract_dir))
            self.assertEqual(win2._options.binwalk_executable, exe)

            idx = win2._preset_combo.findData("custom:Mój profil")
            self.assertGreaterEqual(idx, 0)
            win2._preset_combo.setCurrentIndex(idx)
            self.assertTrue(win2._options.matryoshka)
            self.assertTrue(win2._options.entropy)
            self.assertTrue(win2._delete_preset_btn.isEnabled())

            self.assertTrue(win2.delete_custom_preset("Mój profil"))
            self.assertFalse(win2._delete_preset_btn.isEnabled())
            self.assertEqual(win2._preset_combo.findData("custom:Mój profil"), -1)
            win2.close()

            # Usunięcie katalogu -C i nieistniejąca binarka w QSettings -> bezpieczny fallback
            extract_dir.rmdir()
            s3 = QSettings(str(ini_path), QSettings.Format.IniFormat)
            s3.setValue("options/binwalk_executable", str(tmp / "missing_binwalk"))
            s3.setValue("options/directory", str(extract_dir))
            s3.sync()

            win3 = MainWindow(settings=s3, presets_path=presets_path)
            win3.show()
            self.assertEqual(win3._options.directory, "")
            self.assertEqual(win3._options.binwalk_executable, default_binwalk_executable())
            win3.close()


if __name__ == "__main__":
    unittest.main()
