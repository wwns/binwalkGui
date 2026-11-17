"""Okno dialogowe diagnostyki zewnętrznych narzędzi rozpakowujących (ekstraktorów)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..extractors import ExtractorStatus, check_extractors


class ExtractorCheckDialog(QDialog):
    """Wyświetla dostępność zewnętrznych ekstraktorów binwalk oraz wskazówki instalacji."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        path_env: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._path_env = path_env
        self._statuses: list[ExtractorStatus] = []

        self.setWindowTitle("Sprawdź ekstraktory Binwalk")
        self.resize(940, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        self._summary_label = QLabel()
        self._summary_label.setObjectName("sectionTitle")
        header.addWidget(self._summary_label)
        header.addStretch()

        info_label = QLabel("Uwzględnia ~/.local/bin oraz /usr/local/bin w PATH")
        info_label.setObjectName("mutedLabel")
        header.addWidget(info_label)
        root.addLayout(header)

        self._table = QTableWidget(0, 5, self)
        self._table.setHorizontalHeaderLabels(
            ["Narzędzie", "Status", "Ścieżka", "Zastosowanie", "Wskazówka instalacji"]
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._sync_copy_button)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(2, 200)
        self._table.setColumnWidth(3, 240)
        root.addWidget(self._table, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)

        self._refresh_btn = QPushButton("Odśwież")
        self._refresh_btn.setToolTip("Ponownie sprawdza dostępność ekstraktorów w PATH.")
        self._refresh_btn.clicked.connect(self.refresh)
        footer.addWidget(self._refresh_btn)

        self._copy_btn = QPushButton("Kopiuj komendę instalacji")
        self._copy_btn.setToolTip("Kopiuje polecenie instalacji dla zaznaczonego narzędzia.")
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self.copy_selected_hint)
        footer.addWidget(self._copy_btn)

        self._feedback_label = QLabel()
        self._feedback_label.setObjectName("mutedLabel")
        footer.addWidget(self._feedback_label, 1)

        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        root.addLayout(footer)

        self.refresh()

    def refresh(self) -> None:
        """Odświeża listę ekstraktorów i zawartość tabeli."""
        self._statuses = check_extractors(self._path_env)
        self._table.setRowCount(len(self._statuses))

        available_count = 0
        for row, status in enumerate(self._statuses):
            if status.available:
                available_count += 1

            cmd_item = QTableWidgetItem(status.info.command)
            cmd_item.setFlags(cmd_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, cmd_item)

            status_item = QTableWidgetItem("Dostępny" if status.available else "Brak")
            status_item.setForeground(
                QColor("#51cf66") if status.available else QColor("#fcc419")
            )
            self._table.setItem(row, 1, status_item)

            path_text = status.path or "—"
            path_item = QTableWidgetItem(path_text)
            path_item.setToolTip(path_text)
            self._table.setItem(row, 2, path_item)

            purpose_item = QTableWidgetItem(status.info.purpose)
            purpose_item.setToolTip(status.info.purpose)
            self._table.setItem(row, 3, purpose_item)

            hint_item = QTableWidgetItem(status.info.install_hint)
            hint_item.setToolTip(status.info.install_hint)
            self._table.setItem(row, 4, hint_item)

        self._summary_label.setText(
            f"Dostępne ekstraktory: {available_count} / {len(self._statuses)}"
        )
        self._sync_copy_button()

    def copy_selected_hint(self) -> bool:
        """Kopiuje wskazówkę instalacji zaznaczonego ekstraktora do schowka."""
        row = self._table.currentRow()
        if not 0 <= row < len(self._statuses):
            return False
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False
        status = self._statuses[row]
        clipboard.setText(status.info.install_hint)
        self._feedback_label.setText(f"Skopiowano instrukcję dla: {status.info.command}")
        return True

    def _sync_copy_button(self) -> None:
        row = self._table.currentRow()
        self._copy_btn.setEnabled(0 <= row < len(self._statuses))
