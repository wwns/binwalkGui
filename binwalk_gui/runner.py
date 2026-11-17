"""Asynchroniczne uruchamianie procesu binwalk w Qt (QProcess) z wykrywaniem wyników."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, pyqtSignal

from .extractors import build_augmented_path


@dataclass(frozen=True)
class RunArtifacts:
    """Artefakty wykryte po zakończeniu działania procesu binwalk."""

    exit_code: int
    working_dir: str
    extracted_dirs: list[str]
    png_plots: list[str]


def _scan_dir_mtime(directory: str, suffix: str, want_dir: bool) -> dict[str, float]:
    """Zwraca mapę {ścieżka: mtime} dla elementów o podanym przyrostku w katalogu."""
    found: dict[str, float] = {}
    if not directory or not os.path.isdir(directory):
        return found
    try:
        for entry in os.scandir(directory):
            if not entry.name.endswith(suffix):
                continue
            if want_dir and not entry.is_dir():
                continue
            if not want_dir and not entry.is_file():
                continue
            try:
                found[entry.path] = entry.stat().st_mtime
            except OSError:
                continue
    except OSError:
        pass
    return found


class BinwalkRunner(QObject):
    """Zarządza pojedynczym wykonaniem polecenia binwalk bez blokowania GUI."""

    started_run = pyqtSignal(str)
    stdout_received = pyqtSignal(str)
    stderr_received = pyqtSignal(str)
    finished_run = pyqtSignal(object)  # RunArtifacts
    failed_start = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process: QProcess | None = None
        self._working_dir = ""
        self._search_dirs: list[str] = []
        self._before_extracted: dict[str, float] = {}
        self._before_pngs: dict[str, float] = {}
        self._kill_timer = QTimer(self)
        self._kill_timer.setSingleShot(True)
        self._kill_timer.timeout.connect(self._force_kill)

    def is_running(self) -> bool:
        """Sprawdza, czy proces binwalk nadal działa."""
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def start_run(
        self,
        argv: list[str],
        working_dir: str,
        extra_output_dir: str = "",
    ) -> None:
        """Uruchamia polecenie binwalk w osobnym procesie."""
        if self.is_running():
            self.failed_start.emit("Proces binwalk już trwa. Zatrzymaj go przed kolejnym uruchomieniem.")
            return
        if not argv:
            self.failed_start.emit("Pusta lista argumentów polecenia.")
            return

        self._working_dir = working_dir or os.getcwd()
        if not os.path.isdir(self._working_dir):
            self._working_dir = os.getcwd()
        self._search_dirs = []
        for candidate in (extra_output_dir.strip(), self._working_dir):
            if candidate and candidate not in self._search_dirs:
                self._search_dirs.append(candidate)

        self._before_extracted = {}
        self._before_pngs = {}
        for d in self._search_dirs:
            self._before_extracted.update(_scan_dir_mtime(d, ".extracted", want_dir=True))
            self._before_pngs.update(_scan_dir_mtime(d, ".png", want_dir=False))

        process = QProcess(self)
        process.setWorkingDirectory(self._working_dir)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PATH", build_augmented_path(env.value("PATH")))
        process.setProcessEnvironment(env)

        process.readyReadStandardOutput.connect(self._on_stdout)
        process.readyReadStandardError.connect(self._on_stderr)
        process.finished.connect(self._on_finished)
        process.errorOccurred.connect(self._on_error)

        self._process = process
        program, args = argv[0], argv[1:]
        self.started_run.emit(self._working_dir)
        process.start(program, args)

    def stop_run(self) -> None:
        """Zatrzymuje uruchomiony proces (najpierw SIGTERM, po 2 s SIGKILL)."""
        if not self.is_running() or self._process is None:
            return
        self._process.terminate()
        self._kill_timer.start(2000)

    def terminate_on_close(self) -> None:
        """Natychmiastowo kończy proces przy zamykaniu okna aplikacji."""
        self._kill_timer.stop()
        if not self.is_running() or self._process is None:
            return
        self._process.terminate()
        if not self._process.waitForFinished(500):
            self._process.kill()
            self._process.waitForFinished(500)

    def _force_kill(self) -> None:
        if self.is_running() and self._process is not None:
            self._process.kill()

    def _on_stdout(self) -> None:
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if data:
            self.stdout_received.emit(data)

    def _on_stderr(self) -> None:
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        if data:
            self.stderr_received.emit(data)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            msg = "Nie udało się uruchomić binwalk. Sprawdź ścieżkę do pliku wykonywalnego."
            self._process = None
            self.failed_start.emit(msg)

    def _on_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self._kill_timer.stop()
        self._on_stdout()
        self._on_stderr()

        extracted = self._collect_changed_items(".extracted", True, self._before_extracted)
        pngs = self._collect_changed_items(".png", False, self._before_pngs)
        self._process = None

        self.finished_run.emit(
            RunArtifacts(
                exit_code=exit_code,
                working_dir=self._working_dir,
                extracted_dirs=extracted,
                png_plots=pngs,
            )
        )

    def _collect_changed_items(
        self,
        suffix: str,
        want_dir: bool,
        before: dict[str, float],
    ) -> list[str]:
        after: dict[str, float] = {}
        for d in self._search_dirs:
            after.update(_scan_dir_mtime(d, suffix, want_dir=want_dir))

        changed = [
            path
            for path, mtime in after.items()
            if path not in before
            or mtime > before[path]
            or (want_dir and _dir_has_newer_entries(path, before[path]))
        ]

        return sorted(changed, key=lambda p: after.get(p, 0.0), reverse=True)


def _dir_has_newer_entries(directory: str, threshold_mtime: float) -> bool:
    """Sprawdza, czy w katalogu pojawiły się lub zostały zmodyfikowane pliki po starcie."""
    try:
        for entry in os.scandir(directory):
            try:
                if entry.stat().st_mtime > threshold_mtime:
                    return True
            except OSError:
                continue
    except OSError:
        pass
    return False


def guess_default_extract_root(target_files: list[str], custom_dir: str) -> str:
    """Wyznacza bazowy katalog podglądu rozpakowanych plików."""
    if custom_dir.strip() and os.path.isdir(custom_dir.strip()):
        return custom_dir.strip()
    if target_files:
        first = Path(target_files[0]).resolve()
        candidate = first.parent / f"_{first.name}.extracted"
        if candidate.is_dir():
            return str(candidate)
        if first.parent.is_dir():
            return str(first.parent)
    return os.getcwd()
