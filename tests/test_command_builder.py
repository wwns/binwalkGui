"""Testy jednostkowe modelu opcji i budowania poleceń CLI Binwalk."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from binwalk_gui.command_builder import (
    build_command,
    format_command_preview,
    parse_float_value,
    parse_int_or_hex,
    resolve_working_directory,
    validate_options,
)
from binwalk_gui.models import OPTION_SPECS, PRESETS, BinwalkOptions, apply_preset


class TestCommandBuilder(unittest.TestCase):
    def test_all_54_cli_flags_covered(self) -> None:
        """Sprawdza, czy każda z 54 flag CLI generuje poprawny argument."""
        self.assertEqual(len(OPTION_SPECS), 54)

        opts = BinwalkOptions(binwalk_executable="/usr/bin/binwalk", target_files=["fw.bin"])
        for spec in OPTION_SPECS:
            if spec.kind == "bool":
                setattr(opts, spec.field_name, True)
            elif spec.kind in ("list", "list_file"):
                setattr(opts, spec.field_name, ["val1", "val2"])
            elif spec.kind == "float":
                setattr(opts, spec.field_name, "0.9")
            elif spec.kind == "int_hex":
                setattr(opts, spec.field_name, "0x10")
            else:
                setattr(opts, spec.field_name, "testval")

        short_argv = build_command(opts)
        self.assertEqual(short_argv[0], "/usr/bin/binwalk")
        self.assertEqual(short_argv[-1], "fw.bin")
        for spec in OPTION_SPECS:
            self.assertIn(spec.short_flag, short_argv)
            if spec.kind in ("list", "list_file"):
                self.assertEqual(short_argv.count(spec.short_flag), 2)

        opts.use_long_flags = True
        long_argv = build_command(opts)
        for spec in OPTION_SPECS:
            self.assertIn(spec.long_flag, long_argv)
            if spec.kind in ("list", "list_file"):
                self.assertEqual(long_argv.count(spec.long_flag), 2)

    def test_empty_defaults_produce_clean_command(self) -> None:
        opts = BinwalkOptions(binwalk_executable="binwalk", target_files=["router.bin"])
        self.assertEqual(build_command(opts), ["binwalk", "router.bin"])

    def test_repeatable_dd_and_filters(self) -> None:
        opts = BinwalkOptions(
            binwalk_executable="binwalk",
            extract=True,
            dd_rules=["squashfs:sqsh:unsquashfs %e", "gzip:gz"],
            exclude_filters=["copyright", "zeros"],
            include_filters=["elf"],
            target_files=["a.bin", "b.bin"],
        )
        argv = build_command(opts)
        self.assertEqual(
            argv,
            [
                "binwalk",
                "-e",
                "-D",
                "squashfs:sqsh:unsquashfs %e",
                "-D",
                "gzip:gz",
                "-x",
                "copyright",
                "-x",
                "zeros",
                "-y",
                "elf",
                "a.bin",
                "b.bin",
            ],
        )
        preview = format_command_preview(argv)
        self.assertIn("'squashfs:sqsh:unsquashfs %e'", preview)

    def test_parse_int_or_hex_and_float(self) -> None:
        self.assertEqual(parse_int_or_hex("4096"), 4096)
        self.assertEqual(parse_int_or_hex("0x1000"), 4096)
        self.assertAlmostEqual(parse_float_value("0,95"), 0.95)
        with self.assertRaises(ValueError):
            parse_int_or_hex("0xZZ")

    def test_validation_errors_and_warnings(self) -> None:
        opts = BinwalkOptions(target_files=[])
        errors, _ = validate_options(opts)
        self.assertTrue(errors)

        with tempfile.NamedTemporaryFile() as tmp:
            bad = BinwalkOptions(
                target_files=[tmp.name],
                offset="-5",
                entropy_high="abc",
                preserve_symlinks=True,
                csv=True,
                entropy=True,
            )
            errors, warnings = validate_options(bad)
            self.assertEqual(len(errors), 2)
            self.assertEqual(len(warnings), 3)

    def test_presets_and_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fw = Path(tmpdir) / "firmware.bin"
            fw.write_bytes(b"TEST")
            base = BinwalkOptions(
                binwalk_executable="/usr/bin/binwalk",
                target_files=[str(fw)],
                signature=True,
            )
            updated = apply_preset(base, "Głębokie rozpakowanie (-e -M)")
            self.assertTrue(updated.extract)
            self.assertTrue(updated.matryoshka)
            self.assertFalse(updated.signature)
            self.assertEqual(updated.target_files, [str(fw)])
            self.assertEqual(resolve_working_directory(updated), tmpdir)
            self.assertIn("Wyczyść wszystkie opcje", PRESETS)


if __name__ == "__main__":
    unittest.main()
