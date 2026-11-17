"""Wielokrotnego użytku kontrolki UI dla Binwalk GUI."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..command_builder import parse_float_value, parse_int_or_hex


class FileDropListWidget(QWidget):
    """Lista plików wejściowych z obsługą Drag & Drop oraz zmianą kolejności."""

    filesChanged = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("Pliki wejściowe (.bin / firmware) — przeciągnij i upuść tutaj:")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel("0 plików")
        self._count_label.setObjectName("mutedLabel")
        header.addWidget(self._count_label)
        root.addLayout(header)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.setMinimumHeight(88)
        self._list.setMaximumHeight(130)
        self._list.setToolTip(
            "Upuść tutaj jeden lub więcej plików .bin (kolejność ma znaczenie przy diffie -W)."
        )
        self._list.itemSelectionChanged.connect(self._sync_buttons)
        QShortcut(
            QKeySequence(Qt.Key.Key_Delete),
            self._list,
            activated=self._remove_selected,
            context=Qt.ShortcutContext.WidgetShortcut,
        )
        root.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._add_btn = QPushButton("Dodaj plik(i)...")
        self._add_btn.setToolTip("Wybierz pliki binarne do analizy lub rozpakowania (Ctrl+O).")
        self._add_btn.clicked.connect(self.browse_files)
        btn_row.addWidget(self._add_btn)

        self._up_btn = QPushButton("W górę")
        self._up_btn.setToolTip("Przesuń zaznaczony plik wyżej na liście.")
        self._up_btn.clicked.connect(lambda: self._move_selected(-1))
        btn_row.addWidget(self._up_btn)

        self._down_btn = QPushButton("W dół")
        self._down_btn.setToolTip("Przesuń zaznaczony plik niżej na liście.")
        self._down_btn.clicked.connect(lambda: self._move_selected(1))
        btn_row.addWidget(self._down_btn)

        self._remove_btn = QPushButton("Usuń zaznaczone")
        self._remove_btn.setToolTip("Usuń zaznaczone pliki z listy (Delete).")
        self._remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(self._remove_btn)

        self._clear_btn = QPushButton("Wyczyść")
        self._clear_btn.setToolTip("Usuń wszystkie pliki z listy.")
        self._clear_btn.clicked.connect(self.clear)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch()

        root.addLayout(btn_row)
        self._sync_buttons()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: list[str] = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and os.path.isfile(local):
                paths.append(local)
        if paths:
            self.add_files(paths)
            event.acceptProposedAction()

    def files(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def set_files(self, paths: list[str]) -> None:
        self._list.clear()
        for p in paths:
            if p:
                self._list.addItem(p)
        self._sync_count()
        self.filesChanged.emit(self.files())

    def add_files(self, paths: list[str]) -> None:
        existing = set(self.files())
        added = False
        for p in paths:
            norm = os.path.abspath(p)
            if norm not in existing and os.path.isfile(norm):
                self._list.addItem(norm)
                existing.add(norm)
                added = True
        if added:
            self._sync_count()
            self.filesChanged.emit(self.files())

    def clear(self) -> None:
        if self._list.count() == 0:
            return
        self._list.clear()
        self._sync_count()
        self.filesChanged.emit([])

    def browse_files(self) -> None:
        """Otwiera okno wyboru plików binarnych."""
        self._browse_files()

    def _browse_files(self) -> None:
        start_dir = str(Path(self.files()[0]).parent) if self.files() else str(Path.home())
        selected, _ = QFileDialog.getOpenFileNames(
            self,
            "Wybierz pliki binarne do analizy / rozpakowania",
            start_dir,
            "Pliki firmware (*.bin *.img *.fw *.rom *.ubi *.squashfs *.trx);;Wszystkie pliki (*)",
        )
        if selected:
            self.add_files(selected)

    def _remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self._list.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for row in rows:
            self._list.takeItem(row)
        self._sync_count()
        self.filesChanged.emit(self.files())

    def _move_selected(self, delta: int) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        target = row + delta
        if not 0 <= target < self._list.count():
            return
        item = self._list.takeItem(row)
        self._list.insertItem(target, item)
        self._list.setCurrentRow(target)
        self.filesChanged.emit(self.files())

    def _sync_count(self) -> None:
        n = self._list.count()
        if n == 1:
            self._count_label.setText("1 plik")
        elif 2 <= n <= 4:
            self._count_label.setText(f"{n} pliki")
        else:
            self._count_label.setText(f"{n} plików")
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        count = self._list.count()
        selected_rows = {idx.row() for idx in self._list.selectedIndexes()}
        current_row = self._list.currentRow()
        has_single_selection = len(selected_rows) == 1 and current_row >= 0
        self._up_btn.setEnabled(has_single_selection and current_row > 0)
        self._down_btn.setEnabled(has_single_selection and current_row < count - 1)
        self._remove_btn.setEnabled(bool(selected_rows))
        self._clear_btn.setEnabled(count > 0)


class PathPicker(QWidget):
    """Pole ścieżki z przyciskiem wyboru pliku lub katalogu."""

    textChanged = pyqtSignal(str)

    def __init__(
        self,
        mode: str,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(True)
        self._edit.textChanged.connect(self.textChanged)
        layout.addWidget(self._edit, 1)

        self._btn = QPushButton("Wybierz...")
        self._btn.setToolTip("Otwórz okno wyboru ścieżki.")
        self._btn.clicked.connect(self._browse)
        layout.addWidget(self._btn)

    def text(self) -> str:
        return self._edit.text()

    def setText(self, value: str) -> None:
        if self._edit.text() != value:
            self._edit.setText(value)

    def _initial_browse_dir(self) -> str:
        raw = self._edit.text().strip()
        if not raw:
            return str(Path.home())
        candidate = Path(raw)
        if candidate.is_dir():
            return str(candidate)
        for parent in candidate.parents:
            if parent.is_dir():
                return str(parent)
        return str(Path.home())

    def _browse(self) -> None:
        current = self._initial_browse_dir()
        if self._mode == "dir":
            chosen = QFileDialog.getExistingDirectory(self, "Wybierz katalog", current)
        elif self._mode == "save_file":
            default_target = self._edit.text().strip() or current
            chosen, _ = QFileDialog.getSaveFileName(self, "Wybierz plik zapisu", default_target)
        else:
            chosen, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", current)
        if chosen:
            self._edit.setText(chosen)


class ValidatedLineEdit(QLineEdit):
    """Pole tekstowe z podglądem poprawności formatu dec/hex lub float."""

    def __init__(self, kind: str, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._kind = kind
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.textChanged.connect(self._revalidate)

    def _revalidate(self, text: str) -> None:
        stripped = text.strip()
        is_valid = True
        if stripped:
            try:
                if self._kind == "int_hex":
                    is_valid = parse_int_or_hex(stripped) >= 0
                elif self._kind == "float":
                    parse_float_value(stripped)
            except ValueError:
                is_valid = False
        self.setProperty("invalid", not is_valid)
        self.style().unpolish(self)
        self.style().polish(self)


class RepeatableListEditor(QWidget):
    """Edytor powtarzalnych flag CLI (np. -D, -R, -m, -x, -y)."""

    itemsChanged = pyqtSignal(list)

    def __init__(
        self,
        placeholder: str = "",
        allow_file_browse: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setClearButtonEnabled(True)
        self._input.setToolTip("Wpisz wartość i naciśnij Enter lub kliknij Dodaj.")
        self._input.returnPressed.connect(self._add_current)
        input_row.addWidget(self._input, 1)

        if allow_file_browse:
            browse_btn = QPushButton("Plik...")
            browse_btn.setToolTip("Wybierz plik z dysku.")
            browse_btn.clicked.connect(self._browse_file)
            input_row.addWidget(browse_btn)

        add_btn = QPushButton("Dodaj")
        add_btn.setToolTip("Dodaj wpis do listy.")
        add_btn.clicked.connect(self._add_current)
        input_row.addWidget(add_btn)

        remove_btn = QPushButton("Usuń")
        remove_btn.setToolTip("Usuń zaznaczone wpisy z listy (Delete).")
        remove_btn.clicked.connect(self._remove_selected)
        input_row.addWidget(remove_btn)

        layout.addLayout(input_row)

        self._list = QListWidget()
        self._list.setMaximumHeight(84)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        QShortcut(
            QKeySequence(Qt.Key.Key_Delete),
            self._list,
            activated=self._remove_selected,
            context=Qt.ShortcutContext.WidgetShortcut,
        )
        layout.addWidget(self._list)

    def items(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def set_items(self, values: list[str]) -> None:
        self._list.clear()
        for val in values:
            if val.strip():
                self._list.addItem(val.strip())

    def _add_current(self) -> None:
        val = self._input.text().strip()
        if not val:
            return
        self._list.addItem(val)
        self._input.clear()
        self.itemsChanged.emit(self.items())

    def _browse_file(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Wybierz plik magic", str(Path.home()))
        if chosen:
            self._list.addItem(chosen)
            self.itemsChanged.emit(self.items())

    def _remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self._list.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for row in rows:
            self._list.takeItem(row)
        self.itemsChanged.emit(self.items())
