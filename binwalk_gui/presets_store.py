"""Zapis i odczyt własnych presetów użytkownika w formacie JSON."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .models import PRESETS, SPEC_BY_FIELD, BinwalkOptions


def default_presets_path() -> Path:
    """Zwraca domyślną ścieżkę pliku własnych presetów (~/.config/binwalkGui/presets.json)."""
    return Path.home() / ".config" / "binwalkGui" / "presets.json"


def _resolve_presets_path(presets_path: Path | str | None) -> Path:
    if presets_path is None:
        return default_presets_path()
    return Path(presets_path)


def _normalize_preset_dict(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Filtruje i normalizuje słownik opcji presetu zgodnie z OPTION_SPECS."""
    normalized: dict[str, Any] = {}
    for key, val in raw.items():
        spec = SPEC_BY_FIELD.get(key)
        if spec is None:
            continue
        if spec.kind == "bool":
            if bool(val):
                normalized[key] = True
        elif spec.kind in ("list", "list_file"):
            if isinstance(val, (list, tuple)):
                cleaned_items = [str(item).strip() for item in val if str(item).strip()]
                if cleaned_items:
                    normalized[key] = cleaned_items
        else:
            cleaned = str(val).strip() if val is not None else ""
            if cleaned:
                normalized[key] = cleaned
    return normalized


def options_to_preset_dict(options: BinwalkOptions) -> dict[str, Any]:
    """Serializuje wszystkie ustawione flagi OPTION_SPECS obiektu BinwalkOptions do słownika JSON."""
    data: dict[str, Any] = {}
    for field_name, spec in SPEC_BY_FIELD.items():
        value = getattr(options, field_name)
        if spec.kind == "bool":
            if value:
                data[field_name] = True
        elif spec.kind in ("list", "list_file"):
            cleaned_items = [str(item).strip() for item in value if str(item).strip()]
            if cleaned_items:
                data[field_name] = cleaned_items
        elif isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                data[field_name] = cleaned
    return data


def apply_preset_dict(base: BinwalkOptions, preset_data: Mapping[str, Any]) -> BinwalkOptions:
    """Tworzy nową konfigurację na bazie słownika presetu, zachowując pliki i binarkę."""
    new_opts = BinwalkOptions(
        binwalk_executable=base.binwalk_executable,
        use_long_flags=base.use_long_flags,
        target_files=list(base.target_files),
        directory=base.directory,
    )
    normalized = _normalize_preset_dict(preset_data)
    for key, val in normalized.items():
        setattr(new_opts, key, list(val) if isinstance(val, list) else val)
    return new_opts


def load_custom_presets(presets_path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Wczytuje własne presety z pliku JSON (zwraca {} przy braku lub uszkodzeniu pliku)."""
    path = _resolve_presets_path(presets_path)
    if not path.is_file():
        return {}
    try:
        raw_text = path.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}

    if not isinstance(parsed, dict):
        return {}

    result: dict[str, dict[str, Any]] = {}
    for raw_name, raw_opts in parsed.items():
        name = str(raw_name).strip()
        if not name or name in PRESETS or not isinstance(raw_opts, Mapping):
            continue
        result[name] = _normalize_preset_dict(raw_opts)
    return result


def save_custom_presets(
    presets: Mapping[str, Mapping[str, Any]],
    presets_path: Path | str | None = None,
) -> Path:
    """Zapisuje słownik własnych presetów do pliku JSON."""
    path = _resolve_presets_path(presets_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean_payload = {
        str(name).strip(): _normalize_preset_dict(opts)
        for name, opts in presets.items()
        if str(name).strip() and str(name).strip() not in PRESETS
    }
    path.write_text(
        json.dumps(clean_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def save_custom_preset(
    name: str,
    options: BinwalkOptions,
    presets_path: Path | str | None = None,
) -> dict[str, dict[str, Any]]:
    """Dodaje lub nadpisuje pojedynczy własny preset i zwraca zaktualizowaną mapę."""
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValueError("Nazwa presetu nie może być pusta.")
    if cleaned_name in PRESETS:
        raise ValueError(f"Nazwa '{cleaned_name}' jest zarezerwowana dla presetu wbudowanego.")

    presets = load_custom_presets(presets_path)
    presets[cleaned_name] = options_to_preset_dict(options)
    save_custom_presets(presets, presets_path)
    return presets


def delete_custom_preset(
    name: str,
    presets_path: Path | str | None = None,
) -> dict[str, dict[str, Any]]:
    """Usuwa własny preset (wbudowane presety są ignorowane) i zwraca zaktualizowaną mapę."""
    cleaned_name = name.strip()
    presets = load_custom_presets(presets_path)
    if cleaned_name and cleaned_name not in PRESETS and cleaned_name in presets:
        del presets[cleaned_name]
        save_custom_presets(presets, presets_path)
    return presets
