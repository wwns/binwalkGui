"""Panel wyników: konsola wyjścia na żywo, eksplorator rozpakowanych plików i wykres PNG."""

from __future__ import annotations

import html
import os
from pathlib import Path

from PyQt6.QtCore import QDir, QModelIndex, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFileSystemModel, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QTabWidget,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ..ansi import ansi_to_html


class ResultsViewWidget(QWidget):
    """Prawy panel prezentujący logi binwalka, rozpakowane pliki oraz wykres entropii."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_extract_dir = os.getcwd()
        self._current_pixmap: QPixmap | None = None
        self._dark_mode = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        self._tabs.addTab(self._build_console_tab(), "Konsola wyjścia")
        self._tabs.addTab(self._build_files_tab(), "Rozpakowane pliki")
        self._tabs.addTab(self._build_entropy_tab(), "Wykres entropii")

    def _build_console_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        info = QLabel("Strumień wyjścia binwalk (obsługa kolorów ANSI diff -W):")
        info.setObjectName("mutedLabel")
        bar.addWidget(info)
        bar.addStretch()

        clear_btn = QPushButton("Wyczyść konsolę")
        clear_btn.setToolTip("Czyści bieżące wyjście konsoli (Ctrl+L).")
        clear_btn.clicked.connect(self.clear_console)
        bar.addWidget(clear_btn)

        save_btn = QPushButton("Zapisz log...")
        save_btn.setToolTip("Zapisuje zawartość konsoli do pliku .log / .txt (Ctrl+S).")
        save_btn.clicked.connect(self.save_console_log)
        bar.addWidget(save_btn)
        layout.addLayout(bar)

        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setObjectName("consoleView")
        self._console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._console.document().setMaximumBlockCount(20000)
        layout.addWidget(self._console, 1)

        return tab

    def _build_files_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._dir_display = QLineEdit()
        self._dir_display.setReadOnly(True)
        self._dir_display.setToolTip("Aktualny katalog podglądu rozpakowanych plików.")
        toolbar.addWidget(self._dir_display, 1)

        choose_btn = QPushButton("Folder...")
        choose_btn.setToolTip("Wybierz inny katalog do podglądu.")
        choose_btn.clicked.connect(self._browse_extract_dir)
        toolbar.addWidget(choose_btn)

        self._refresh_btn = QPushButton("Odśwież")
        self._refresh_btn.setToolTip("Odświeża drzewo rozpakowanych plików.")
        self._refresh_btn.clicked.connect(self.refresh_files_view)
        toolbar.addWidget(self._refresh_btn)

        self._open_folder_btn = QPushButton("Otwórz w menedżerze")
        self._open_folder_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self._open_folder_btn.setToolTip("Otwiera bieżący katalog w systemowym menedżerze plików.")
        self._open_folder_btn.clicked.connect(self.open_current_folder)
        toolbar.addWidget(self._open_folder_btn)

        copy_btn = QPushButton("Kopiuj ścieżkę")
        copy_btn.setToolTip("Kopiuje ścieżkę bieżącego katalogu do schowka.")
        copy_btn.clicked.connect(self._copy_current_folder)
        toolbar.addWidget(copy_btn)
        layout.addLayout(toolbar)

        self._missing_dir_bar = QFrame()
        self._missing_dir_bar.setObjectName("card")
        missing_layout = QHBoxLayout(self._missing_dir_bar)
        missing_layout.setContentsMargins(10, 8, 10, 8)
        missing_layout.setSpacing(8)
        self._missing_dir_label = QLabel()
        self._missing_dir_label.setObjectName("warningLabel")
        self._missing_dir_label.setWordWrap(True)
        missing_layout.addWidget(self._missing_dir_label, 1)
        create_dir_btn = QPushButton("Utwórz katalog")
        create_dir_btn.setToolTip("Tworzy brakujący katalog docelowy na dysku.")
        create_dir_btn.clicked.connect(self._create_current_extract_dir)
        missing_layout.addWidget(create_dir_btn)
        self._missing_dir_bar.setVisible(False)
        layout.addWidget(self._missing_dir_bar)

        self._fs_model = QFileSystemModel(self)
        self._fs_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)

        self._tree = QTreeView()
        self._tree.setModel(self._fs_model)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.setAlternatingRowColors(True)
        self._tree.doubleClicked.connect(self._open_tree_item)
        self._tree.setColumnWidth(0, 280)
        layout.addWidget(self._tree, 1)

        self.set_extract_directory(self._current_extract_dir)
        return tab

    def _build_entropy_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Wygenerowany wykres:"))

        self._png_combo = QComboBox()
        self._png_combo.currentTextChanged.connect(self._load_png_preview)
        bar.addWidget(self._png_combo, 1)

        open_img_btn = QPushButton("Otwórz obraz")
        open_img_btn.setToolTip("Otwiera wybrany wykres PNG w zewnętrznej przeglądarce obrazów.")
        open_img_btn.clicked.connect(self._open_selected_png)
        bar.addWidget(open_img_btn)
        layout.addLayout(bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._png_label = QLabel(
            "Brak wczytanego wykresu.\nUruchom analizę entropii z flagami -E -J (opcjonalnie -N), aby zapisać i wyświetlić wykres PNG."
        )
        self._png_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._png_label.setObjectName("mutedLabel")
        scroll.setWidget(self._png_label)
        layout.addWidget(scroll, 1)

        return tab

    def set_dark_mode(self, dark: bool) -> None:
        """Ustawia tryb kolorystyczny (jasny/ciemny) dla wyjścia ANSI i banerów konsoli."""
        self._dark_mode = bool(dark)

    def banner_color(self, kind: str = "info") -> str:
        """Zwraca kontrastowy kolor banera dla aktualnego trybu konsoli."""
        if self._dark_mode:
            return {
                "info": "#74c0fc",
                "success": "#51cf66",
                "error": "#ff6b6b",
                "warning": "#fcc419",
            }.get(kind, "#74c0fc")
        return {
            "info": "#1864ab",
            "success": "#2b8a3e",
            "error": "#c92a2a",
            "warning": "#b45309",
        }.get(kind, "#1864ab")

    def clear_console(self) -> None:
        self._console.clear()

    def append_output(self, text: str, is_stderr: bool = False) -> None:
        normalized = text.replace("\r\n", "\n")
        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if is_stderr and "\x1b[" not in normalized:
            stderr_color = "#ff8787" if self._dark_mode else "#c92a2a"
            escaped = html.escape(normalized).replace("\n", "<br>")
            html_chunk = f'<span style="color:{stderr_color}">{escaped}</span>'
        else:
            html_chunk = ansi_to_html(normalized, dark=self._dark_mode)
        cursor.insertHtml(html_chunk)
        self._console.setTextCursor(cursor)
        self._console.ensureCursorVisible()

    def append_banner(self, message: str, color: str | None = None) -> None:
        resolved_color = color if color is not None else self.banner_color("info")
        cursor = self._console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        escaped = html.escape(message).replace("\n", "<br>")
        cursor.insertHtml(f'<div style="color:{resolved_color};font-weight:bold">{escaped}</div>')
        self._console.setTextCursor(cursor)
        self._console.ensureCursorVisible()

    def set_extract_directory(self, directory: str) -> None:
        cleaned = directory.strip()
        if not cleaned:
            return
        self._current_extract_dir = cleaned
        self._dir_display.setText(cleaned)
        if os.path.isdir(cleaned):
            self._missing_dir_bar.setVisible(False)
            self._tree.setVisible(True)
            self._open_folder_btn.setEnabled(True)
            self._refresh_btn.setEnabled(True)
            root_idx = self._fs_model.setRootPath(cleaned)
            self._tree.setRootIndex(root_idx)
        else:
            self._missing_dir_label.setText(
                f"Katalog jeszcze nie istnieje: {cleaned}. "
                "Zostanie utworzony podczas rozpakowywania (-e) lub utwórz go ręcznie."
            )
            self._missing_dir_bar.setVisible(True)
            self._tree.setVisible(False)
            self._open_folder_btn.setEnabled(False)
            self._refresh_btn.setEnabled(False)

    def refresh_files_view(self) -> None:
        if os.path.isdir(self._current_extract_dir):
            self._missing_dir_bar.setVisible(False)
            self._tree.setVisible(True)
            self._open_folder_btn.setEnabled(True)
            self._refresh_btn.setEnabled(True)
            # Ponowne ustawienie ścieżki wymusza odświeżenie drzewa
            self._fs_model.setRootPath("")
            root_idx = self._fs_model.setRootPath(self._current_extract_dir)
            self._tree.setRootIndex(root_idx)
        else:
            self.set_extract_directory(self._current_extract_dir)

    def show_console_tab(self) -> None:
        self._tabs.setCurrentIndex(0)

    def show_files_tab(self) -> None:
        self._tabs.setCurrentIndex(1)

    def show_entropy_tab(self) -> None:
        self._tabs.setCurrentIndex(2)

    def show_tab(self, index: int) -> None:
        """Przełącza widok wyników na wskazaną zakładkę."""
        if 0 <= index < self._tabs.count():
            self._tabs.setCurrentIndex(index)

    def set_entropy_plots(self, png_paths: list[str]) -> None:
        self._png_combo.blockSignals(True)
        self._png_combo.clear()
        for p in png_paths:
            if os.path.isfile(p):
                self._png_combo.addItem(p)
        self._png_combo.blockSignals(False)
        count = self._png_combo.count()
        self._tabs.setTabText(2, f"Wykres entropii ({count})" if count else "Wykres entropii")
        if count > 0:
            self._load_png_preview(self._png_combo.currentText())

    def _load_png_preview(self, path: str) -> None:
        if not path or not os.path.isfile(path):
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._png_label.setText(f"Nie udało się wczytać obrazu: {path}")
            return
        self._current_pixmap = pixmap
        self._png_label.setPixmap(pixmap)

    def _open_selected_png(self) -> None:
        path = self._png_combo.currentText()
        if path and os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _browse_extract_dir(self) -> None:
        start_dir = self._current_extract_dir
        if not os.path.isdir(start_dir):
            parent = next((str(p) for p in Path(start_dir).parents if p.is_dir()), os.getcwd())
            start_dir = parent
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Wybierz folder z rozpakowanymi plikami",
            start_dir,
        )
        if chosen:
            self.set_extract_directory(chosen)

    def _create_current_extract_dir(self) -> None:
        target = self._current_extract_dir.strip()
        if not target:
            return
        try:
            Path(target).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Błąd tworzenia katalogu",
                f"Nie udało się utworzyć katalogu '{target}':\n{exc}",
            )
            return
        self.set_extract_directory(target)

    def open_current_folder(self) -> None:
        if os.path.isdir(self._current_extract_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._current_extract_dir))

    def _copy_current_folder(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._current_extract_dir)

    def _open_tree_item(self, index: QModelIndex) -> None:
        path = self._fs_model.filePath(index)
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def save_console_log(self) -> None:
        """Zapisuje zawartość konsoli wyjścia do pliku tekstowego."""
        self._save_console_log()

    def _save_console_log(self) -> None:
        base_dir = (
            self._current_extract_dir
            if os.path.isdir(self._current_extract_dir)
            else os.getcwd()
        )
        default_path = str(Path(base_dir) / "binwalk_output.log")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz log konsoli",
            default_path,
            "Pliki tekstowe (*.log *.txt);;Wszystkie pliki (*)",
        )
        if path:
            try:
                Path(path).write_text(self._console.toPlainText(), encoding="utf-8")
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    "Błąd zapisu logu",
                    f"Nie udało się zapisać pliku '{path}':\n{exc}",
                )
