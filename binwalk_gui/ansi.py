"""Konwerter sekwencji kolorów ANSI (np. wyjście diff binwalk -W) na bezpieczny HTML."""

from __future__ import annotations

import html
import re

ANSI_SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")

ANSI_FG_COLORS: dict[int, str] = {
    30: "#555753",
    31: "#ff6b6b",
    32: "#51cf66",
    33: "#fcc419",
    34: "#74c0fc",
    35: "#da77f2",
    36: "#3bc9db",
    37: "#e9ecef",
    90: "#868e96",
    91: "#ff8787",
    92: "#69db7c",
    93: "#ffe066",
    94: "#91a7ff",
    95: "#e599f7",
    96: "#66d9e8",
    97: "#ffffff",
}

ANSI_FG_COLORS_LIGHT: dict[int, str] = {
    30: "#1f2328",
    31: "#c92a2a",
    32: "#2b8a3e",
    33: "#b45309",
    34: "#1864ab",
    35: "#9c36b5",
    36: "#0b7285",
    37: "#495057",
    90: "#57606a",
    91: "#e03131",
    92: "#2f9e44",
    93: "#d97706",
    94: "#1d4ed8",
    95: "#ae3ec9",
    96: "#0c8599",
    97: "#1f2328",
}


def strip_ansi(text: str) -> str:
    """Usuwa wszystkie kody sterujące ANSI SGR z tekstu."""
    return ANSI_SGR_RE.sub("", text)


def ansi_to_html(text: str, *, dark: bool = True) -> str:
    """Konwertuje tekst z kodami ANSI SGR na HTML gotowy do osadzenia w QTextEdit."""
    palette = ANSI_FG_COLORS if dark else ANSI_FG_COLORS_LIGHT
    parts: list[str] = []
    pos = 0
    fg_color: str | None = None
    bold = False

    def wrap_segment(segment: str) -> str:
        escaped = html.escape(segment).replace("\n", "<br>")
        if not escaped:
            return ""
        styles: list[str] = []
        if fg_color:
            styles.append(f"color:{fg_color}")
        if bold:
            styles.append("font-weight:bold")
        if styles:
            return f'<span style="{";".join(styles)}">{escaped}</span>'
        return escaped

    for match in ANSI_SGR_RE.finditer(text):
        if match.start() > pos:
            parts.append(wrap_segment(text[pos : match.start()]))
        pos = match.end()

        codes_raw = match.group(1)
        codes = [int(c) for c in codes_raw.split(";") if c.isdigit()] if codes_raw else [0]
        for code in codes:
            if code == 0:
                fg_color = None
                bold = False
            elif code == 1:
                bold = True
            elif code == 22:
                bold = False
            elif code == 39:
                fg_color = None
            elif code in palette:
                fg_color = palette[code]

    if pos < len(text):
        parts.append(wrap_segment(text[pos:]))

    return "".join(parts)
