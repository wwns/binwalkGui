"""Skórki i style UI dla Binwalk GUI (jasny klasyczny PeaZip, ciemny i systemowy)."""

from __future__ import annotations

from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QWidget

THEME_LABELS: dict[str, str] = {
    "light": "Jasny klasyczny (PeaZip)",
    "dark": "Ciemny (Dark)",
    "system": "Systemowy (Qt/XFCE)",
}

DEFAULT_THEME_ID = "light"

LIGHT_STYLESHEET = """
QMainWindow, QWidget, QDialog {
    background-color: #f4f5f7;
    color: #1f2328;
    font-size: 13px;
}
QFrame#card, QFrame#optionRow {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
}
QLabel#sectionTitle {
    font-weight: 600;
    color: #1f2328;
}
QLabel#mutedLabel, QLabel#optionHint {
    color: #57606a;
    font-size: 12px;
}
QLabel#warningLabel {
    color: #b45309;
    font-size: 12px;
}
QLineEdit, QListWidget, QTextEdit, QTreeView, QComboBox, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 5px;
    padding: 5px 7px;
    color: #1f2328;
    selection-background-color: #dbeafe;
    selection-color: #1d4ed8;
}
QListWidget, QTreeView, QTableWidget {
    alternate-background-color: #f8f9fb;
}
QTableWidget {
    gridline-color: #d0d7de;
}
QListWidget::item:selected, QTreeView::item:selected, QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1d4ed8;
}
QLineEdit:focus, QListWidget:focus, QComboBox:focus, QTextEdit:focus, QTreeView:focus {
    border-color: #2563eb;
}
QLineEdit[invalid="true"] {
    border-color: #cf222e;
    background-color: #fff5f5;
}
QTextEdit#consoleView, QLineEdit#commandPreview {
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 12px;
    background-color: #ffffff;
    color: #1f2328;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 5px;
    padding: 6px 12px;
    color: #1f2328;
}
QPushButton:hover {
    background-color: #eef1f4;
    border-color: #bbc3cd;
}
QPushButton:pressed {
    background-color: #e5e9ef;
}
QPushButton:disabled {
    background-color: #f6f8fa;
    color: #8c959f;
    border-color: #e1e6eb;
}
QPushButton#primaryBtn {
    background-color: #d97706;
    border-color: #b45309;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#primaryBtn:hover {
    background-color: #b45309;
}
QPushButton#primaryBtn:disabled {
    background-color: #f3d09e;
    border-color: #e6be83;
    color: #ffffff;
}
QPushButton#secondaryActionBtn {
    background-color: #2b8a3e;
    border-color: #237032;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#secondaryActionBtn:hover {
    background-color: #237032;
}
QPushButton#secondaryActionBtn:disabled {
    background-color: #a3cfa9;
    border-color: #93c299;
    color: #ffffff;
}
QPushButton#dangerBtn {
    background-color: #c92a2a;
    border-color: #a61e1e;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#dangerBtn:hover {
    background-color: #a61e1e;
}
QPushButton#dangerBtn:disabled {
    background-color: #e5a5a5;
    border-color: #d99595;
    color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #ffffff;
}
QTabBar::tab {
    background-color: #eaeef2;
    border: 1px solid #d0d7de;
    color: #57606a;
    padding: 6px 12px;
    margin-right: 2px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1f2328;
    font-weight: 600;
    border-bottom-color: #1d4ed8;
}
QHeaderView::section {
    background-color: #f4f5f7;
    color: #1f2328;
    border: none;
    border-right: 1px solid #d0d7de;
    border-bottom: 1px solid #d0d7de;
    padding: 5px 8px;
    font-weight: 600;
}
QMenuBar {
    background-color: #f4f5f7;
    border-bottom: 1px solid #d0d7de;
    padding: 2px 4px;
    color: #1f2328;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #dbeafe;
    color: #1d4ed8;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    padding: 4px;
    color: #1f2328;
}
QMenu::item {
    padding: 5px 22px 5px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #dbeafe;
    color: #1d4ed8;
}
QMenu::item:disabled {
    color: #8c959f;
}
QMenu::separator {
    height: 1px;
    background-color: #d0d7de;
    margin: 4px 6px;
}
QToolTip {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d0d7de;
    padding: 4px 6px;
}
"""

DARK_STYLESHEET = """
QMainWindow, QWidget, QDialog {
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
QLineEdit, QListWidget, QTextEdit, QTreeView, QComboBox, QTableWidget {
    background-color: #11141c;
    border: 1px solid #2f374d;
    border-radius: 5px;
    padding: 5px 7px;
    color: #e6e9ef;
}
QTableWidget {
    alternate-background-color: #181c27;
    gridline-color: #2b3245;
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
QHeaderView::section {
    background-color: #1e2330;
    color: #e6e9ef;
    border: none;
    border-right: 1px solid #2b3245;
    border-bottom: 1px solid #2b3245;
    padding: 5px 8px;
    font-weight: 600;
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

SYSTEM_STYLESHEET = """
QFrame#card, QFrame#optionRow {
    border: 1px solid palette(mid);
    border-radius: 6px;
}
QLabel#sectionTitle {
    font-weight: 600;
}
QLabel#mutedLabel, QLabel#optionHint {
    font-size: 12px;
}
QLabel#warningLabel {
    color: #b45309;
    font-size: 12px;
}
QLineEdit[invalid="true"] {
    border: 1px solid #cf222e;
    background-color: rgba(207, 34, 46, 0.12);
}
QTextEdit#consoleView, QLineEdit#commandPreview {
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 12px;
}
QPushButton#primaryBtn {
    font-weight: 600;
}
QPushButton#secondaryActionBtn {
    font-weight: 600;
}
QPushButton#dangerBtn {
    font-weight: 600;
}
"""

THEMES: dict[str, str] = {
    "light": LIGHT_STYLESHEET,
    "dark": DARK_STYLESHEET,
    "system": SYSTEM_STYLESHEET,
}


def normalize_theme_id(theme_id: str | None) -> str:
    """Normalizuje identyfikator skórki do jednej ze wspieranych wartości."""
    if isinstance(theme_id, str) and theme_id in THEMES:
        return theme_id
    return DEFAULT_THEME_ID


def apply_theme(theme_id: str, target_widget: QWidget | None = None) -> str:
    """Stosuje wskazaną skórkę na QApplication (lub widget zastępczy) i zwraca jej ID."""
    normalized = normalize_theme_id(theme_id)
    stylesheet = THEMES[normalized]

    app = QApplication.instance()
    if isinstance(app, QApplication):
        app.setStyle("Fusion")
        app.setProperty("binwalk_theme", normalized)
        app.setStyleSheet(stylesheet)
        if target_widget is not None:
            target_widget.setProperty("binwalk_theme", normalized)
            target_widget.setStyleSheet("")
    elif target_widget is not None:
        target_widget.setProperty("binwalk_theme", normalized)
        target_widget.setStyleSheet(stylesheet)

    return normalized


def is_dark_theme(
    theme_id: str | QWidget | None = None,
    widget: QWidget | None = None,
) -> bool:
    """Określa, czy aktywna lub podana skórka ma ciemne tło."""
    resolved_widget = widget
    resolved_id: str | None

    if isinstance(theme_id, QWidget):
        resolved_widget = theme_id
        prop = resolved_widget.property("binwalk_theme")
        if not prop and isinstance(QApplication.instance(), QApplication):
            prop = QApplication.instance().property("binwalk_theme")
        resolved_id = str(prop) if prop else "system"
    else:
        resolved_id = theme_id

    if resolved_id == "dark":
        return True
    if resolved_id == "light":
        return False

    palette: QPalette | None = None
    if resolved_widget is not None:
        palette = resolved_widget.palette()
    elif isinstance(QApplication.instance(), QApplication):
        palette = QApplication.instance().palette()

    if palette is None:
        return False
    return palette.color(QPalette.ColorRole.Window).lightness() < 128
