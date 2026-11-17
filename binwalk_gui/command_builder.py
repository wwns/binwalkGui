"""Budowanie i walidacja poleceń CLI narzędzia binwalk."""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

from .models import OPTION_SPECS, BinwalkOptions, OptionSpec


def detect_binwalk_executables() -> list[str]:
    """Zwraca listę wykrytych plików wykonywalnych binwalka (najpełniejszy pierwszy)."""
    candidates: list[str] = []
    preferred = [
        "/usr/bin/binwalk",
        shutil.which("binwalk") or "",
        str(Path.home() / ".local" / "bin" / "binwalk"),
    ]
    for path in preferred:
        if path and os.path.isfile(path) and os.access(path, os.X_OK) and path not in candidates:
            candidates.append(path)
    return candidates or ["binwalk"]


def default_binwalk_executable() -> str:
    """Zwraca domyślną ścieżkę wykonywalną binwalka."""
    return detect_binwalk_executables()[0]


def parse_int_or_hex(raw: str) -> int:
    """Parsuje liczbę całkowitą w formacie dziesiętnym lub szesnastkowym (np. 0x1000)."""
    text = raw.strip()
    if not text:
        raise ValueError("Pusta wartość liczbowa")
    return int(text, 0)


def parse_float_value(raw: str) -> float:
    """Parsuje liczbę zmiennoprzecinkową (akceptuje przecinek lub kropkę)."""
    text = raw.strip().replace(",", ".")
    if not text:
        raise ValueError("Pusta wartość zmiennoprzecinkowa")
    return float(text)


def _flag_for(spec: OptionSpec, use_long_flags: bool) -> str:
    return spec.long_flag if use_long_flags else spec.short_flag


def validate_options(options: BinwalkOptions) -> tuple[list[str], list[str]]:
    """Waliduje opcje przed uruchomieniem. Zwraca (błędy, ostrzeżenia)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not options.show_help and not options.target_files:
        errors.append("Wybierz co najmniej jeden plik .bin (lub włącz -h / --help).")

    for file_path in options.target_files:
        if not os.path.exists(file_path):
            errors.append(f"Plik nie istnieje: {file_path}")

    if not options.binwalk_executable.strip():
        errors.append("Ścieżka do pliku wykonywalnego binwalk nie może być pusta.")

    custom_dir = options.directory.strip()
    if custom_dir and os.path.exists(custom_dir) and not os.path.isdir(custom_dir):
        errors.append(f"Ścieżka katalogu -C (--directory) nie jest katalogiem: {custom_dir}")

    for spec in OPTION_SPECS:
        value = getattr(options, spec.field_name)
        if spec.kind == "int_hex" and isinstance(value, str) and value.strip():
            try:
                parsed = parse_int_or_hex(value)
                if parsed < 0:
                    errors.append(f"Opcja {spec.short_flag} ({spec.long_flag}) nie może być ujemna.")
            except ValueError:
                errors.append(
                    f"Nieprawidłowa liczba dla {spec.short_flag} ({spec.long_flag}): '{value}'."
                )
        elif spec.kind == "float" and isinstance(value, str) and value.strip():
            try:
                parsed_f = parse_float_value(value)
                if not 0.0 <= parsed_f <= 1.0:
                    warnings.append(
                        f"Wartość {spec.short_flag} ({parsed_f}) wykracza poza typowy zakres entropii 0.0–1.0."
                    )
            except ValueError:
                errors.append(
                    f"Nieprawidłowa liczba zmiennoprzecinkowa dla {spec.short_flag}: '{value}'."
                )

    if options.preserve_symlinks:
        warnings.append(
            "Włączono -1 (--preserve-symlinks): symlinki wskazujące poza katalog ekstrakcji nie będą czyszczone."
        )

    if options.csv and not options.log_file.strip():
        warnings.append("Włączono -c (--csv) bez pliku logu -f (--log) — zapis CSV wymaga podania pliku -f.")

    if options.entropy and not options.nplot and not options.save_plot:
        warnings.append(
            "Włączono -E (--entropy) bez -N (--nplot): binwalk może próbować otworzyć osobne okno wykresu."
        )

    return errors, warnings


def build_command(options: BinwalkOptions) -> list[str]:
    """Buduje listę argumentów CLI dla QProcess / subprocess (bez shell=True)."""
    exe = options.binwalk_executable.strip() or "binwalk"
    argv: list[str] = [exe]
    long_mode = options.use_long_flags

    for spec in OPTION_SPECS:
        value = getattr(options, spec.field_name)
        flag = _flag_for(spec, long_mode)

        if spec.kind == "bool":
            if value:
                argv.append(flag)
        elif spec.kind in ("list", "list_file"):
            for item in value:
                cleaned = item.strip()
                if cleaned:
                    argv.extend([flag, cleaned])
        elif spec.kind == "float":
            if isinstance(value, str) and value.strip():
                normalized = value.strip().replace(",", ".")
                argv.extend([flag, normalized])
        elif isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                argv.extend([flag, cleaned])

    argv.extend(options.target_files)
    return argv


def format_command_preview(argv: list[str]) -> str:
    """Formatuje polecenie CLI do bezpiecznego podglądu i kopiowania."""
    return shlex.join(argv)


def resolve_working_directory(options: BinwalkOptions) -> str:
    """Wyznacza katalog roboczy procesu binwalk (domyślnie obok pierwszego pliku .bin)."""
    custom_dir = options.directory.strip()
    if custom_dir and os.path.isdir(custom_dir):
        return custom_dir
    if options.target_files:
        first_parent = str(Path(options.target_files[0]).resolve().parent)
        if os.path.isdir(first_parent):
            return first_parent
    return os.getcwd()
