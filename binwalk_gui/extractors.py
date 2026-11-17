"""Wykrywanie i diagnostyka zewnętrznych narzędzi rozpakowujących dla Binwalk."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractorInfo:
    """Metadane zewnętrznego narzędzia rozpakowującego używanego przez binwalk."""

    command: str
    purpose: str
    install_hint: str


@dataclass(frozen=True)
class ExtractorStatus:
    """Wynik sprawdzenia dostępności pojedynczego ekstraktora w systemie."""

    info: ExtractorInfo
    available: bool
    path: str | None


EXTRACTOR_SPECS: tuple[ExtractorInfo, ...] = (
    ExtractorInfo(
        command="jefferson",
        purpose="Rozpakowywanie systemów plików JFFS2",
        install_hint=(
            "python3 -m venv ~/.local/share/jefferson-venv && "
            "~/.local/share/jefferson-venv/bin/pip install jefferson && "
            "ln -sf ~/.local/share/jefferson-venv/bin/jefferson ~/.local/bin/jefferson"
        ),
    ),
    ExtractorInfo(
        command="sasquatch",
        purpose="Niestandardowe / zmodyfikowane obrazy SquashFS",
        install_hint="Zbuduj z github.com/devttys0/sasquatch (zainstaluj do /usr/local/bin lub ~/.local/bin)",
    ),
    ExtractorInfo(
        command="unsquashfs",
        purpose="Standardowe systemy plików SquashFS",
        install_hint="sudo apt install squashfs-tools",
    ),
    ExtractorInfo(
        command="ubireader_extract_files",
        purpose="Systemy plików UBIFS / UBI",
        install_hint="pipx install ubi_reader  (lub pip install ubi-reader w venv)",
    ),
    ExtractorInfo(
        command="cramfsck",
        purpose="Systemy plików CramFS",
        install_hint="sudo apt install cramfsswap  (lub util-linux / pakiet cramfsprogs)",
    ),
    ExtractorInfo(
        command="7z",
        purpose="Archiwa 7z, LZMA, ZIP, XZ, CAB i inne kontenery",
        install_hint="sudo apt install p7zip-full",
    ),
    ExtractorInfo(
        command="tar",
        purpose="Archiwa TAR",
        install_hint="sudo apt install tar",
    ),
    ExtractorInfo(
        command="gzip",
        purpose="Strumienie i archiwa GZIP",
        install_hint="sudo apt install gzip",
    ),
    ExtractorInfo(
        command="bzip2",
        purpose="Strumienie i archiwa BZIP2",
        install_hint="sudo apt install bzip2",
    ),
    ExtractorInfo(
        command="xz",
        purpose="Strumienie i archiwa XZ / LZMA",
        install_hint="sudo apt install xz-utils",
    ),
    ExtractorInfo(
        command="lzop",
        purpose="Strumienie i archiwa LZO",
        install_hint="sudo apt install lzop",
    ),
    ExtractorInfo(
        command="cabextract",
        purpose="Archiwa Microsoft Cabinet (.cab)",
        install_hint="sudo apt install cabextract",
    ),
    ExtractorInfo(
        command="unrar",
        purpose="Archiwa RAR",
        install_hint="sudo apt install unrar  (lub unrar-free)",
    ),
    ExtractorInfo(
        command="unstuff",
        purpose="Archiwa StuffIt (.sit)",
        install_hint="Zainstaluj pakiet StuffIt Expander / binarkę unstuff w PATH",
    ),
)


def build_augmented_path(base_path: str | None = None) -> str:
    """Buduje zmienną PATH wzbogaconą o ~/.local/bin i /usr/local/bin bez duplikatów."""
    raw = os.environ.get("PATH", "") if base_path is None else base_path
    parts: list[str] = []
    seen: set[str] = set()

    def _add(entry: str) -> None:
        cleaned = entry.strip()
        if not cleaned or cleaned in seen:
            return
        seen.add(cleaned)
        parts.append(cleaned)

    for segment in raw.split(os.pathsep):
        _add(segment)

    _add(str(Path.home() / ".local" / "bin"))
    _add("/usr/local/bin")
    return os.pathsep.join(parts)


def check_extractors(path_env: str | None = None) -> list[ExtractorStatus]:
    """Sprawdza dostępność wszystkich zdefiniowanych ekstraktorów w rozszerzonym PATH."""
    search_path = build_augmented_path(path_env)
    statuses: list[ExtractorStatus] = []
    for spec in EXTRACTOR_SPECS:
        resolved = shutil.which(spec.command, path=search_path)
        statuses.append(
            ExtractorStatus(
                info=spec,
                available=resolved is not None,
                path=resolved,
            )
        )
    return statuses
