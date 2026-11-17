#!/usr/bin/env python3
"""Punkt wejścia aplikacji Binwalk GUI."""

from __future__ import annotations

import sys

from binwalk_gui.ui.main_window import run_app

if __name__ == "__main__":
    raise SystemExit(run_app(sys.argv[1:]))
