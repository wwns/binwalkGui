"""Panel 7 zakładek ze wszystkimi opcjami Binwalk v2.4.3 oraz wyszukiwarką opcji."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..models import CATEGORIES, OPTION_SPECS, BinwalkOptions, OptionSpec
from .widgets import PathPicker, RepeatableListEditor, ValidatedLineEdit


@dataclass
class _OptionBinding:
    spec: OptionSpec
    row_widget: QWidget
    control: QWidget
    search_blob: str


class OptionTabsWidget(QWidget):
    """Generuje zakładki wszystkich opcji CLI na podstawie OPTION_SPECS."""

    optionsChanged = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._syncing = False
        self._bindings: dict[str, _OptionBinding] = {}
        self._tab_layouts: dict[str, QVBoxLayout] = {}
        self._tab_indices: dict[str, int] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self._search = QLineEdit()
        self._search.setPlaceholderText(
            "Szukaj dowolnej opcji (np. -M, matryoshka, dd, entropy, offset, -W)... [Ctrl+F]"
        )
        self._search.setToolTip("Filtruje opcje po nazwie, fladze CLI lub opisie (Ctrl+F).")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_search_filter)
        QShortcut(
            QKeySequence(Qt.Key.Key_Escape),
            self._search,
            activated=self.clear_search,
            context=Qt.ShortcutContext.WidgetShortcut,
        )
        root.addWidget(self._search)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        root.addWidget(self._tabs, 1)

        self._build_tabs()

    def _build_tabs(self) -> None:
        for cat_key, cat_title in CATEGORIES:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)

            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(8, 8, 8, 8)
            vbox.setSpacing(10)

            for spec in OPTION_SPECS:
                if spec.category != cat_key:
                    continue
                row = self._create_option_row(spec)
                vbox.addWidget(row)

            vbox.addStretch()
            scroll.setWidget(container)

            idx = self._tabs.addTab(scroll, cat_title)
            self._tab_layouts[cat_key] = vbox
            self._tab_indices[cat_key] = idx

    def _create_option_row(self, spec: OptionSpec) -> QWidget:
        row = QFrame()
        row.setObjectName("optionRow")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        if spec.kind == "bool":
            control: QWidget = QCheckBox(spec.label)
            control.setToolTip(spec.tooltip)
            control.toggled.connect(self._on_control_changed)
            layout.addWidget(control)
        else:
            lbl = QLabel(spec.label)
            lbl.setWordWrap(True)
            lbl.setToolTip(spec.tooltip)
            layout.addWidget(lbl)

            if spec.kind in ("int_hex", "float"):
                control = ValidatedLineEdit(spec.kind, spec.placeholder)
                control.setToolTip(spec.tooltip)
                control.textChanged.connect(self._on_control_changed)
            elif spec.kind in ("file", "dir", "save_file"):
                control = PathPicker(spec.kind, spec.placeholder)
                control.setToolTip(spec.tooltip)
                control.textChanged.connect(self._on_control_changed)
            elif spec.kind in ("list", "list_file"):
                control = RepeatableListEditor(
                    placeholder=spec.placeholder,
                    allow_file_browse=(spec.kind == "list_file"),
                )
                control.setToolTip(spec.tooltip)
                control.itemsChanged.connect(self._on_control_changed)
            else:
                control = QLineEdit()
                control.setPlaceholderText(spec.placeholder)
                control.setClearButtonEnabled(True)
                control.setToolTip(spec.tooltip)
                control.textChanged.connect(self._on_control_changed)

            layout.addWidget(control)

        hint = QLabel(spec.tooltip)
        hint.setObjectName("optionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        if spec.warning:
            warn = QLabel(spec.warning)
            warn.setObjectName("warningLabel")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        blob = " ".join(
            [
                spec.short_flag,
                spec.long_flag,
                spec.label,
                spec.tooltip,
                spec.field_name,
            ]
        ).lower()
        self._bindings[spec.field_name] = _OptionBinding(
            spec=spec,
            row_widget=row,
            control=control,
            search_blob=blob,
        )
        return row

    def focus_search(self) -> None:
        """Ustawia fokus na polu wyszukiwania opcji i zaznacza tekst."""
        self._search.setFocus()
        self._search.selectAll()

    def clear_search(self) -> None:
        """Czyści filtr wyszukiwania opcji."""
        self._search.clear()

    def _on_control_changed(self, *_args: object) -> None:
        if not self._syncing:
            self.optionsChanged.emit()

    def apply_to_options(self, options: BinwalkOptions) -> None:
        """Zapisuje stan wszystkich kontrolek do przekazanego obiektu BinwalkOptions."""
        for field_name, binding in self._bindings.items():
            ctrl = binding.control
            kind = binding.spec.kind
            if kind == "bool" and isinstance(ctrl, QCheckBox):
                setattr(options, field_name, ctrl.isChecked())
            elif kind in ("list", "list_file") and isinstance(ctrl, RepeatableListEditor):
                setattr(options, field_name, ctrl.items())
            elif isinstance(ctrl, PathPicker):
                setattr(options, field_name, ctrl.text().strip())
            elif isinstance(ctrl, QLineEdit):
                setattr(options, field_name, ctrl.text().strip())

    def load_from_options(self, options: BinwalkOptions) -> None:
        """Aktualizuje wszystkie kontrolki na podstawie obiektu BinwalkOptions."""
        self._syncing = True
        try:
            for field_name, binding in self._bindings.items():
                ctrl = binding.control
                kind = binding.spec.kind
                val = getattr(options, field_name)
                if kind == "bool" and isinstance(ctrl, QCheckBox):
                    ctrl.setChecked(bool(val))
                elif kind in ("list", "list_file") and isinstance(ctrl, RepeatableListEditor):
                    ctrl.set_items(list(val))
                elif isinstance(ctrl, PathPicker):
                    ctrl.setText(str(val))
                elif isinstance(ctrl, QLineEdit):
                    if ctrl.text() != str(val):
                        ctrl.setText(str(val))
        finally:
            self._syncing = False

    def _apply_search_filter(self, raw_query: str) -> None:
        query = raw_query.strip().lower()
        counts: dict[str, int] = {cat_key: 0 for cat_key, _ in CATEGORIES}

        for binding in self._bindings.values():
            matches = (not query) or (query in binding.search_blob)
            binding.row_widget.setVisible(matches)
            if matches:
                counts[binding.spec.category] += 1

        first_match_idx: int | None = None
        for cat_key, cat_title in CATEGORIES:
            idx = self._tab_indices[cat_key]
            if query:
                n = counts[cat_key]
                self._tabs.setTabText(idx, f"{cat_title} ({n})")
                if n > 0 and first_match_idx is None:
                    first_match_idx = idx
            else:
                self._tabs.setTabText(idx, cat_title)

        current_idx = self._tabs.currentIndex()
        if (
            query
            and first_match_idx is not None
            and 0 <= current_idx < len(CATEGORIES)
            and counts[CATEGORIES[current_idx][0]] == 0
        ):
            self._tabs.setCurrentIndex(first_match_idx)
