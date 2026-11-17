"""Główne okno aplikacji Binwalk GUI (PyQt6)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import __version__

from ..command_builder import (
    build_command,
    default_binwalk_executable,
    detect_binwalk_executables,
    format_command_preview,
    resolve_working_directory,
    validate_options,
)
from ..models import PRESETS, BinwalkOptions, apply_preset
from ..runner import BinwalkRunner, RunArtifacts, guess_default_extract_root
from .option_tabs import OptionTabsWidget
from .results_view import ResultsViewWidget
from .widgets import FileDropListWidget, PathPicker

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #161922;
    color: #e6e9ef;
    font-size: 13px;
}
QFrame#card, QFrame#optionRow {
    background-color: #1e2330;
    border: 1px solid #2b3245;
    border-radius: 6px;
}
QLabel#sectionTitle {
    font-weight: 600;
    color: #ffffff;
}
QLabel#mutedLabel, QLabel#optionHint {
    color: #9aa5be;
    font-size: 12px;
}
QLabel#warningLabel {
    color: #fcc419;
    font-size: 12px;
}
QLineEdit, QListWidget, QTextEdit, QTreeView, QComboBox {
    background-color: #11141c;
    border: 1px solid #2f374d;
    border-radius: 5px;
    padding: 5px 7px;
    color: #e6e9ef;
}
QLineEdit:focus, QListWidget:focus, QComboBox:focus {
    border-color: #4dabf7;
}
QLineEdit[invalid="true"] {
    border-color: #ff6b6b;
    background-color: #26161b;
}
QTextEdit#consoleView, QLineEdit#commandPreview {
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 12px;
}
QPushButton {
    background-color: #272e40;
    border: 1px solid #3a445e;
    border-radius: 5px;
    padding: 6px 12px;
    color: #e6e9ef;
}
QPushButton:hover {
    background-color: #323b52;
}
QPushButton:disabled {
    background-color: #1b202c;
    color: #677189;
}
QPushButton#primaryBtn {
    background-color: #228be6;
    border-color: #339af0;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #1c7ed6;
}
QPushButton#secondaryActionBtn {
    background-color: #2b8a3e;
    border-color: #37b24d;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#secondaryActionBtn:hover {
    background-color: #2f9e44;
}
QPushButton#dangerBtn {
    background-color: #c92a2a;
    border-color: #e03131;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#dangerBtn:hover {
    background-color: #e03131;
}
QTabWidget::pane {
    border: 1px solid #2b3245;
    border-radius: 6px;
    background-color: #181c27;
}
QTabBar::tab {
    background-color: #1e2330;
    border: 1px solid #2b3245;
    padding: 6px 12px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QTabBar::tab:selected {
    background-color: #273047;
    color: #ffffff;
    border-bottom-color: #4dabf7;
}
QMenuBar {
    background-color: #11141c;
    border-bottom: 1px solid #2b3245;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #273047;
    color: #ffffff;
}
QMenu {
    background-color: #1e2330;
    border: 1px solid #2f374d;
    padding: 4px;
}
QMenu::item {
    padding: 5px 22px 5px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #228be6;
    color: #ffffff;
}
QMenu::item:disabled {
    color: #677189;
}
QMenu::separator {
    height: 1px;
    background-color: #2b3245;
    margin: 4px 6px;
}
QToolTip {
    background-color: #1e2330;
    color: #e6e9ef;
    border: 1px solid #3a445e;
    padding: 4px 6px;
}
"""


class MainWindow(QMainWindow):
    """Główne okno GUI dla Binwalk v2.4.3."""

    def __init__(self, initial_files: list[str] | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Binwalk GUI — Rozpakowywanie i analiza plików .bin")
        self.resize(1340, 860)
        self.setAcceptDrops(True)

        self._syncing_quick = False
        self._options = BinwalkOptions(
            binwalk_executable=default_binwalk_executable(),
            extract=True,
        )
        self._runner = BinwalkRunner(self)
        self._runner.started_run.connect(self._on_run_started)
        self._runner.stdout_received.connect(lambda t: self._results.append_output(t, False))
        self._runner.stderr_received.connect(lambda t: self._results.append_output(t, True))
        self._runner.finished_run.connect(self._on_run_finished)
        self._runner.failed_start.connect(self._on_run_failed)

        self._build_ui()
        self._build_menu_bar()
        self._option_tabs.load_from_options(self._options)
        self._sync_quick_controls_from_options()
        if initial_files:
            self._file_list.add_files(initial_files)
        self._update_command_preview()

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&Plik")
        add_files_action = QAction("Dodaj pliki .bin...", self)
        add_files_action.setShortcut(QKeySequence("Ctrl+O"))
        add_files_action.setToolTip("Dodaj pliki binarne do listy wejściowej.")
        add_files_action.triggered.connect(self._file_list.browse_files)
        file_menu.addAction(add_files_action)

        clear_files_action = QAction("Wyczyść listę plików", self)
        clear_files_action.triggered.connect(self._file_list.clear)
        file_menu.addAction(clear_files_action)

        save_log_action = QAction("Zapisz log konsoli...", self)
        save_log_action.setShortcut(QKeySequence("Ctrl+S"))
        save_log_action.triggered.connect(self._results.save_console_log)
        file_menu.addAction(save_log_action)

        file_menu.addSeparator()
        quit_action = QAction("Zakończ", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        actions_menu = menu_bar.addMenu("&Akcje")
        self._unpack_action = QAction("Rozpakuj teraz (-e)", self)
        self._unpack_action.setShortcuts(
            [
                QKeySequence("F5"),
                QKeySequence("Ctrl+Return"),
                QKeySequence("Ctrl+Enter"),
            ]
        )
        self._unpack_action.triggered.connect(self._quick_unpack)
        actions_menu.addAction(self._unpack_action)

        self._scan_action = QAction("Skanuj sygnatury (-B)", self)
        self._scan_action.setShortcut(QKeySequence("F6"))
        self._scan_action.triggered.connect(self._quick_scan)
        actions_menu.addAction(self._scan_action)

        self._run_action = QAction("Uruchom wybrane opcje", self)
        self._run_action.setShortcuts(
            [
                QKeySequence("Ctrl+Shift+Return"),
                QKeySequence("Ctrl+Shift+Enter"),
            ]
        )
        self._run_action.triggered.connect(self._run_current_options)
        actions_menu.addAction(self._run_action)

        self._stop_action = QAction("Zatrzymaj proces", self)
        self._stop_action.setShortcut(QKeySequence("Escape"))
        self._stop_action.setEnabled(False)
        self._stop_action.triggered.connect(self._runner.stop_run)
        actions_menu.addAction(self._stop_action)

        actions_menu.addSeparator()
        self._cli_help_action = QAction("Pokaż pomoc Binwalk CLI (-h)", self)
        self._cli_help_action.setShortcut(QKeySequence("F1"))
        self._cli_help_action.triggered.connect(self._show_cli_help)
        actions_menu.addAction(self._cli_help_action)

        view_menu = menu_bar.addMenu("&Widok")
        search_action = QAction("Szukaj opcji...", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(self._option_tabs.focus_search)
        view_menu.addAction(search_action)

        clear_console_action = QAction("Wyczyść konsolę", self)
        clear_console_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_console_action.triggered.connect(self._results.clear_console)
        view_menu.addAction(clear_console_action)

        copy_cmd_action = QAction("Kopiuj komendę CLI", self)
        copy_cmd_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        copy_cmd_action.triggered.connect(self._copy_command)
        view_menu.addAction(copy_cmd_action)

        reset_opts_action = QAction("Resetuj wszystkie opcje", self)
        reset_opts_action.setShortcut(QKeySequence("Ctrl+R"))
        reset_opts_action.triggered.connect(self._reset_options)
        view_menu.addAction(reset_opts_action)

        view_menu.addSeparator()
        console_tab_action = QAction("Konsola wyjścia", self)
        console_tab_action.setShortcut(QKeySequence("Ctrl+1"))
        console_tab_action.triggered.connect(self._results.show_console_tab)
        view_menu.addAction(console_tab_action)

        files_tab_action = QAction("Rozpakowane pliki", self)
        files_tab_action.setShortcut(QKeySequence("Ctrl+2"))
        files_tab_action.triggered.connect(self._results.show_files_tab)
        view_menu.addAction(files_tab_action)

        entropy_tab_action = QAction("Wykres entropii", self)
        entropy_tab_action.setShortcut(QKeySequence("Ctrl+3"))
        entropy_tab_action.triggered.connect(self._results.show_entropy_tab)
        view_menu.addAction(entropy_tab_action)

        help_menu = menu_bar.addMenu("P&omoc")
        help_menu.addAction(self._cli_help_action)

        shortcuts_action = QAction("Skróty klawiszowe...", self)
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)

        about_action = QAction("O programie...", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        main_layout.addWidget(self._build_quick_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(8)

        self._file_list = FileDropListWidget()
        self._file_list.filesChanged.connect(self._on_files_changed)
        left_layout.addWidget(self._file_list)

        self._option_tabs = OptionTabsWidget()
        self._option_tabs.optionsChanged.connect(self._on_tabs_changed)
        left_layout.addWidget(self._option_tabs, 1)

        splitter.addWidget(left_panel)

        self._results = ResultsViewWidget()
        splitter.addWidget(self._results)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter, 1)
        main_layout.addWidget(self._build_command_bar())

    def _build_quick_bar(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self._unpack_btn = QPushButton("Rozpakuj teraz (-e)")
        self._unpack_btn.setObjectName("primaryBtn")
        self._unpack_btn.setToolTip(
            "Automatycznie włącza -e (--extract) i uruchamia rozpakowanie wybranych plików .bin (F5 / Ctrl+Enter)."
        )
        self._unpack_btn.clicked.connect(self._quick_unpack)
        row1.addWidget(self._unpack_btn)

        self._scan_btn = QPushButton("Skanuj sygnatury (-B)")
        self._scan_btn.setObjectName("secondaryActionBtn")
        self._scan_btn.setToolTip("Szybki skan sygnatur (-B) bez rozpakowywania (F6).")
        self._scan_btn.clicked.connect(self._quick_scan)
        row1.addWidget(self._scan_btn)

        self._run_btn = QPushButton("Uruchom wybrane opcje")
        self._run_btn.setToolTip(
            "Uruchamia binwalk dokładnie z opcjami skonfigurowanymi w zakładkach (Ctrl+Shift+Enter)."
        )
        self._run_btn.clicked.connect(self._run_current_options)
        row1.addWidget(self._run_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("dangerBtn")
        self._stop_btn.setToolTip("Zatrzymuje bieżący proces binwalk (Esc).")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._runner.stop_run)
        row1.addWidget(self._stop_btn)

        row1.addSpacing(10)
        row1.addWidget(QLabel("Preset:"))
        self._preset_combo = QComboBox()
        self._preset_combo.setToolTip("Wybierz gotowy zestaw flag CLI dla typowych zadań.")
        self._preset_combo.addItem("— Wybierz preset —")
        for name in PRESETS:
            self._preset_combo.addItem(name)
        self._preset_combo.currentTextChanged.connect(self._on_preset_selected)
        row1.addWidget(self._preset_combo)

        row1.addStretch()

        self._long_flags_cb = QCheckBox("Długie flagi (--extract)")
        self._long_flags_cb.setToolTip("Przełącza podgląd i wykonanie między krótkimi (-e) i długimi (--extract) flagami.")
        self._long_flags_cb.toggled.connect(self._on_quick_toggled)
        row1.addWidget(self._long_flags_cb)

        outer.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        row2.addWidget(QLabel("Folder docelowy (-C):"))
        self._quick_dir = PathPicker("dir", "Domyślnie: obok pliku .bin (_plik.extracted)")
        self._quick_dir.setToolTip("Opcjonalny katalog docelowy dla rozpakowanych plików (-C / --directory).")
        self._quick_dir.textChanged.connect(self._on_quick_dir_changed)
        row2.addWidget(self._quick_dir, 2)

        self._quick_matryoshka = QCheckBox("Rekurencyjnie (-M)")
        self._quick_matryoshka.setToolTip("Rozpakowuje rekurencyjnie zagnieżdżone archiwa (Matryoshka).")
        self._quick_matryoshka.toggled.connect(self._on_quick_toggled)
        row2.addWidget(self._quick_matryoshka)

        self._quick_carve = QCheckBox("Tylko wytnij (-z)")
        self._quick_carve.setToolTip("Wycina surowe fragmenty bez uruchamiania zewnętrznych dekompresorów.")
        self._quick_carve.toggled.connect(self._on_quick_toggled)
        row2.addWidget(self._quick_carve)

        row2.addWidget(QLabel("Binarka:"))
        self._exe_combo = QComboBox()
        self._exe_combo.setEditable(True)
        self._exe_combo.setToolTip("Ścieżka do pliku wykonywalnego binwalk.")
        for exe in detect_binwalk_executables():
            self._exe_combo.addItem(exe)
        self._exe_combo.setCurrentText(self._options.binwalk_executable)
        self._exe_combo.currentTextChanged.connect(self._on_quick_toggled)
        self._exe_combo.setMinimumWidth(190)
        row2.addWidget(self._exe_combo, 1)

        outer.addLayout(row2)
        return card

    def _build_command_bar(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Komenda CLI:"))
        self._cmd_preview = QLineEdit()
        self._cmd_preview.setObjectName("commandPreview")
        self._cmd_preview.setReadOnly(True)
        self._cmd_preview.setToolTip("Podgląd dokładnego polecenia CLI przekazywanego do procesu binwalk.")
        layout.addWidget(self._cmd_preview, 1)

        copy_btn = QPushButton("Kopiuj komendę")
        copy_btn.setToolTip("Kopiuje polecenie CLI do schowka (Ctrl+Shift+C).")
        copy_btn.clicked.connect(self._copy_command)
        layout.addWidget(copy_btn)

        reset_btn = QPushButton("Resetuj opcje")
        reset_btn.setToolTip("Przywraca domyślne puste opcje (Ctrl+R).")
        reset_btn.clicked.connect(self._reset_options)
        layout.addWidget(reset_btn)

        self._status_label = QLabel("Gotowy")
        self._status_label.setObjectName("mutedLabel")
        layout.addWidget(self._status_label)

        return card

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile() and os.path.isfile(url.toLocalFile())
        ]
        if paths:
            self._file_list.add_files(paths)
            event.acceptProposedAction()

    def _collect_options(self) -> BinwalkOptions:
        self._option_tabs.apply_to_options(self._options)
        self._options.target_files = self._file_list.files()
        self._options.binwalk_executable = self._exe_combo.currentText().strip()
        self._options.use_long_flags = self._long_flags_cb.isChecked()
        return self._options

    def _sync_quick_controls_from_options(self) -> None:
        self._syncing_quick = True
        try:
            self._quick_dir.setText(self._options.directory)
            self._quick_matryoshka.setChecked(self._options.matryoshka)
            self._quick_carve.setChecked(self._options.carve)
            self._long_flags_cb.setChecked(self._options.use_long_flags)
            self._exe_combo.setCurrentText(self._options.binwalk_executable)
        finally:
            self._syncing_quick = False

    def _on_files_changed(self, files: list[str]) -> None:
        self._options.target_files = files
        self._update_command_preview()
        if files and not self._options.directory.strip():
            self._results.set_extract_directory(str(Path(files[0]).resolve().parent))

    def _on_tabs_changed(self) -> None:
        if self._syncing_quick:
            return
        self._option_tabs.apply_to_options(self._options)
        self._sync_quick_controls_from_options()
        self._update_command_preview()

    def _on_quick_dir_changed(self, text: str) -> None:
        if self._syncing_quick:
            return
        self._options.directory = text.strip()
        self._option_tabs.load_from_options(self._options)
        self._update_command_preview()

    def _on_quick_toggled(self, *_args: object) -> None:
        if self._syncing_quick:
            return
        self._options.matryoshka = self._quick_matryoshka.isChecked()
        self._options.carve = self._quick_carve.isChecked()
        self._options.use_long_flags = self._long_flags_cb.isChecked()
        self._options.binwalk_executable = self._exe_combo.currentText().strip()
        self._option_tabs.load_from_options(self._options)
        self._update_command_preview()

    def _on_preset_selected(self, preset_name: str) -> None:
        if preset_name not in PRESETS:
            return
        self._options = apply_preset(self._collect_options(), preset_name)
        if preset_name == "Wyczyść wszystkie opcje":
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(0)
            self._preset_combo.blockSignals(False)
        self._option_tabs.load_from_options(self._options)
        self._sync_quick_controls_from_options()
        self._update_command_preview()

    def _reset_options(self) -> None:
        self._options = apply_preset(self._collect_options(), "Wyczyść wszystkie opcje")
        self._preset_combo.setCurrentIndex(0)
        self._option_tabs.load_from_options(self._options)
        self._sync_quick_controls_from_options()
        self._update_command_preview()

    def _update_command_preview(self) -> None:
        opts = self._collect_options()
        argv = build_command(opts)
        self._cmd_preview.setText(format_command_preview(argv))

    def _copy_command(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._cmd_preview.text())
            self._status_label.setText("Skopiowano komendę")

    def _quick_unpack(self) -> None:
        opts = self._collect_options()
        opts.extract = True
        self._option_tabs.load_from_options(opts)
        self._update_command_preview()
        self._execute(opts)

    def _quick_scan(self) -> None:
        opts = self._collect_options()
        opts.extract = False
        opts.signature = True
        self._option_tabs.load_from_options(opts)
        self._update_command_preview()
        self._execute(opts)

    def _run_current_options(self) -> None:
        opts = self._collect_options()
        self._execute(opts)

    def _show_cli_help(self) -> None:
        """Uruchamia binwalk -h bez wymagania plików wejściowych i bez nadpisywania opcji."""
        if self._runner.is_running():
            return
        exe = self._exe_combo.currentText().strip() or self._options.binwalk_executable
        help_opts = BinwalkOptions(
            binwalk_executable=exe,
            use_long_flags=self._long_flags_cb.isChecked(),
            show_help=True,
        )
        self._execute(help_opts)

    def _show_shortcuts_dialog(self) -> None:
        QMessageBox.information(
            self,
            "Skróty klawiszowe",
            (
                "<b>Pliki i nawigacja:</b><br>"
                "• <b>Ctrl+O</b> — Dodaj pliki .bin...<br>"
                "• <b>Delete</b> — Usuń zaznaczony wpis z listy<br>"
                "• <b>Ctrl+F</b> — Szukaj opcji CLI<br>"
                "• <b>Ctrl+1 / 2 / 3</b> — Przełącz zakładkę wyników<br><br>"
                "<b>Uruchamianie i konsola:</b><br>"
                "• <b>F5 / Ctrl+Enter</b> — Rozpakuj teraz (-e)<br>"
                "• <b>F6</b> — Skanuj sygnatury (-B)<br>"
                "• <b>Ctrl+Shift+Enter</b> — Uruchom wybrane opcje<br>"
                "• <b>Esc</b> — Zatrzymaj działający proces<br>"
                "• <b>Ctrl+L</b> — Wyczyść konsolę<br>"
                "• <b>Ctrl+S</b> — Zapisz log konsoli<br>"
                "• <b>Ctrl+Shift+C</b> — Kopiuj komendę CLI<br>"
                "• <b>Ctrl+R</b> — Resetuj wszystkie opcje<br>"
                "• <b>F1</b> — Pomoc Binwalk CLI (-h)"
            ),
        )

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "O programie Binwalk GUI",
            (
                f"<b>Binwalk GUI</b> v{__version__}<br>"
                "Graficzna nakładka PyQt6 dla narzędzia Binwalk v2.4.3 "
                "z obsługą wszystkich 54 flag CLI, presetów, kolorowego podglądu ANSI "
                "oraz eksploratora rozpakowanych plików."
            ),
        )

    def _execute(self, opts: BinwalkOptions) -> None:
        errors, warnings = validate_options(opts)
        if errors:
            QMessageBox.warning(self, "Popraw konfigurację", "\n".join(errors))
            return

        if warnings:
            reply = QMessageBox.question(
                self,
                "Ostrzeżenia przed uruchomieniem",
                "\n".join(warnings) + "\n\nCzy kontynuować?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        custom_dir = opts.directory.strip()
        if (
            custom_dir
            and not opts.show_help
            and (opts.extract or bool(opts.dd_rules))
            and not os.path.isdir(custom_dir)
        ):
            try:
                Path(custom_dir).mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    "Błąd katalogu docelowego",
                    f"Nie udało się utworzyć katalogu docelowego (-C) '{custom_dir}':\n{exc}",
                )
                return

        argv = build_command(opts)
        working_dir = resolve_working_directory(opts)

        self._results.show_console_tab()
        self._results.append_banner(
            f"\n$ {format_command_preview(argv)}\n[Katalog roboczy: {working_dir}]\n"
        )
        self._runner.start_run(
            argv=argv,
            working_dir=working_dir,
            extra_output_dir=opts.directory,
        )

    def _set_running_state(self, running: bool) -> None:
        self._unpack_btn.setEnabled(not running)
        self._scan_btn.setEnabled(not running)
        self._run_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._unpack_action.setEnabled(not running)
        self._scan_action.setEnabled(not running)
        self._run_action.setEnabled(not running)
        self._cli_help_action.setEnabled(not running)
        self._stop_action.setEnabled(running)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._runner.terminate_on_close()
        event.accept()

    def _on_run_started(self, working_dir: str) -> None:
        self._set_running_state(True)
        self._status_label.setText(f"W trakcie... ({working_dir})")

    def _on_run_failed(self, message: str) -> None:
        self._set_running_state(False)
        self._status_label.setText("Błąd uruchomienia")
        self._results.append_banner(f"\n[BŁĄD] {message}\n", color="#ff6b6b")

    def _on_run_finished(self, artifacts: RunArtifacts) -> None:
        self._set_running_state(False)
        color = "#51cf66" if artifacts.exit_code == 0 else "#fcc419"
        self._status_label.setText(f"Zakończono (kod {artifacts.exit_code})")
        self._results.append_banner(
            f"\n[Zakończono z kodem {artifacts.exit_code}]\n",
            color=color,
        )

        if artifacts.extracted_dirs:
            self._results.set_extract_directory(artifacts.extracted_dirs[0])
            if self._options.extract or self._options.dd_rules:
                self._results.show_files_tab()
        else:
            fallback_dir = guess_default_extract_root(
                self._options.target_files,
                self._options.directory,
            )
            self._results.set_extract_directory(fallback_dir)
        self._results.refresh_files_view()

        if artifacts.png_plots:
            self._results.set_entropy_plots(artifacts.png_plots)


def run_app(argv: list[str] | None = None) -> int:
    """Uruchamia pętlę zdarzeń aplikacji PyQt6."""
    args = list(sys.argv[1:] if argv is None else argv)
    app = QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    initial_files = [os.path.abspath(p) for p in args if os.path.isfile(p)]
    window = MainWindow(initial_files=initial_files)
    window.show()
    return app.exec()
