"""Global QSS dark theme for FS25 Manager."""

PALETTE = {
    "primary": "#16a34a",
    "primary_hover": "#15803d",
    "danger": "#7f1d1d",
    "surface": "#1e293b",
    "border": "#334155",
    "text": "#e2e8f0",
    "text_dim": "#94a3b8",
    "muted": "#64748b",
}

DARK_THEME = """
/* ── Global ─────────────────────────────────────────── */
QWidget {
    background-color: #111827;
    color: #e2e8f0;
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0f172a;
}

/* ── Sidebar ─────────────────────────────────────────── */
#Sidebar {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
    min-width: 248px;
    max-width: 248px;
}

#SidebarLogo {
    font-size: 34px;
    font-weight: 700;
    color: #e5e7eb;
    padding: 20px 12px 6px 12px;
    letter-spacing: 0.5px;
}

#SidebarSubtitle {
    font-size: 11px;
    color: #64748b;
    padding: 0 16px 18px 16px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

QLabel#SidebarSection {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 12px 0 4px 32px;
}

QPushButton#NavBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 14px 10px 14px;
    padding-left: 12px;
    font-size: 13px;
    color: #94a3b8;
    margin: 2px 18px 2px 8px;
}

QPushButton#NavBtn:hover {
    background-color: #1e293b;
    color: #e2e8f0;
}

QPushButton#NavBtn[active="true"] {
    background-color: #14532d;
    color: #4ade80;
    font-weight: 600;
}

QPushButton#NavBtn[active="false"] {
    margin: 2px 18px 2px 8px;
}

/* ── Content Area ────────────────────────────────────── */
#ContentArea {
    background-color: #111827;
}

#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f1f5f9;
    padding: 4px 0;
}

#PageSubtitle {
    font-size: 12px;
    color: #64748b;
}

/* ── Stat Cards ─────────────────────────────────────── */
#card_installed, #card_favourited, #card_maps, #card_disk, #card_saves, #card_backups {
    border-radius: 10px;
}

#card_installed { background-color: rgba(76, 175, 80, 0.15); border-bottom: 4px solid #4CAF50; }
#card_favourited { background-color: rgba(255, 193, 7, 0.15); border-bottom: 4px solid #FFC107; }
#card_maps { background-color: rgba(33, 150, 243, 0.15); border-bottom: 4px solid #2196F3; }
#card_disk { background-color: rgba(156, 39, 176, 0.15); border-bottom: 4px solid #9C27B0; }
#card_saves { background-color: rgba(76, 175, 80, 0.15); border-bottom: 4px solid #4CAF50; }
#card_backups { background-color: rgba(33, 150, 243, 0.15); border-bottom: 4px solid #2196F3; }

#card_installed #StatValue, #card_installed #StatIcon { color: #4CAF50; font-weight: bold; font-size: 18pt; border: none; background: transparent; }
#card_favourited #StatValue, #card_favourited #StatIcon { color: #FFC107; font-weight: bold; font-size: 18pt; border: none; background: transparent; }
#card_maps #StatValue, #card_maps #StatIcon { color: #2196F3; font-weight: bold; font-size: 18pt; border: none; background: transparent; }
#card_disk #StatValue, #card_disk #StatIcon { color: #9C27B0; font-weight: bold; font-size: 18pt; border: none; background: transparent; }
#card_saves #StatValue, #card_saves #StatIcon { color: #4CAF50; font-weight: bold; font-size: 18pt; border: none; background: transparent; }
#card_backups #StatValue, #card_backups #StatIcon { color: #2196F3; font-weight: bold; font-size: 18pt; border: none; background: transparent; }

#StatCategory {
    color: #B0B0B0;
    font-size: 13px;
    font-weight: bold;
    background: transparent;
    border: none;
}

#StatValue {
    font-size: 26px;
    font-weight: 700;
    color: #4ade80;
}

#StatLabel {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Search / Filter ─────────────────────────────────── */
QLineEdit#SearchBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #e2e8f0;
    selection-background-color: #4ade80;
    selection-color: #000;
}

QLineEdit#SearchBar:focus {
    border-color: #4ade80;
}

/* ── Mod / Save Cards ─────────────────────────────────── */
#ModCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 3px 4px;
}

#ModCard:hover {
    border-color: #4ade80;
    background-color: #1e3a2e;
}

#ModCard[selected="true"] {
    border-color: #4ade80;
    background-color: #14532d;
}

#ModTitle {
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
}

#ModAuthor {
    font-size: 11px;
    color: #94a3b8;
}

#ModMeta {
    font-size: 11px;
    color: #64748b;
}

/* ── Badges ──────────────────────────────────────────── */
#BadgeEnabled {
    background-color: #14532d;
    color: #4ade80;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

#BadgeDisabled {
    background-color: #3b1111;
    color: #f87171;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 7px 16px;
    color: #e2e8f0;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #4ade80;
}

QPushButton:pressed {
    background-color: #14532d;
}

QPushButton#PrimaryBtn {
    background-color: #16a34a;
    border: 1px solid #4ade80;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 8px;
}

QPushButton#PrimaryBtn:hover {
    background-color: #15803d;
}

QPushButton#DangerBtn {
    background-color: #7f1d1d;
    border: 1px solid #f87171;
    color: #fecaca;
}

QPushButton#DangerBtn:hover {
    background-color: #991b1b;
}

QPushButton#SuccessBtn {
    background-color: #14532d;
    border: 1px solid #4ade80;
    color: #4ade80;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
}

QPushButton#SuccessBtn:hover {
    background-color: #166534;
    color: #86efac;
}

QPushButton#ToolBtn {
    background-color: transparent;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    color: #94a3b8;
}

QPushButton#ToolBtn:hover {
    background-color: #1e293b;
    color: #e2e8f0;
    border-color: #64748b;
}

QPushButton#LaunchBtn {
    background-color: #2ecc71;
    color: #121212;
    font-weight: 700;
    font-size: 16px;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #2ecc71;
    margin: 10px 18px 8px 8px;
}

QPushButton#LaunchBtn:hover {
    background-color: #27ae60;
    border-color: #27ae60;
}

QPushButton#LaunchBtn:pressed {
    background-color: #1e8449;
    border-color: #1e8449;
}

QPushButton#CollapsibleHeader {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    color: #e2e8f0;
    text-align: left;
}

QPushButton#CollapsibleHeader:hover {
    background-color: #1e293b;
    border-color: #4ade80;
}

/* ── New Game Wizard Top Nav ─────────────────────────── */
QWidget#WizardTopNav {
    background-color: #050d10;
    border-bottom: 1px solid #1f2d33;
}

QLabel#WizardStepLabel {
    color: #7f98a0;
    font-size: 22px;
    font-weight: 500;
}

QPushButton#WizardNavSecondaryBtn {
    background-color: transparent;
    border: 1px solid #2c3b41;
    border-radius: 10px;
    color: #d5dee2;
    font-weight: 600;
    padding: 8px 18px;
    min-width: 92px;
}

QPushButton#WizardNavSecondaryBtn:hover {
    background-color: #0f1b20;
    border-color: #3f525a;
}

QPushButton#WizardNavSecondaryBtn:disabled {
    color: #6b7e85;
    border-color: #1e2a2f;
}

QPushButton#WizardNavPrimaryBtn {
    background-color: #5fb428;
    border: 1px solid #8ad45f;
    border-radius: 10px;
    color: #ffffff;
    font-weight: 700;
    padding: 8px 18px;
    min-width: 92px;
}

QPushButton#WizardNavPrimaryBtn:hover {
    background-color: #4ea11e;
    border-color: #98dd72;
}

QPushButton#WizardNavPrimaryBtn:pressed {
    background-color: #418a1a;
}

/* ── Scrollbar ───────────────────────────────────────── */
QScrollBar:vertical {
    background: #111827;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #4ade80;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #111827;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 30px;
}

/* ── Splitter ─────────────────────────────────────────── */
QSplitter::handle {
    background: #1e293b;
    width: 2px;
}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 6px 10px;
    color: #e2e8f0;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #4ade80;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    selection-background-color: #14532d;
    color: #e2e8f0;
    border-radius: 7px;
}

/* ── CheckBox ─────────────────────────────────────────── */
QCheckBox {
    color: #e2e8f0;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 2px solid #334155;
    border-radius: 4px;
    background-color: #1e293b;
}

QCheckBox::indicator:checked {
    background-color: #16a34a;
    border-color: #4ade80;
    image: none;
}

QCheckBox::indicator:hover {
    border-color: #4ade80;
}

/* ── Double Spinbox ────────────────────────────────────── */
QDoubleSpinBox, QSpinBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 6px 10px;
    color: #e2e8f0;
}

QDoubleSpinBox:hover, QSpinBox:hover {
    border-color: #4ade80;
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #334155;
    border: none;
    border-radius: 3px;
    width: 16px;
}

/* ── GroupBox ─────────────────────────────────────────── */
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #94a3b8;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    top: -2px;
}

/* ── Label ────────────────────────────────────────────── */
QLabel {
    background: transparent;
    color: #e2e8f0;
}

/* ── Status Bar ────────────────────────────────────────── */
QStatusBar {
    background-color: #0f172a;
    color: #64748b;
    border-top: 1px solid #1e293b;
    font-size: 11px;
}

/* ── Dialog ────────────────────────────────────────────── */
QDialog {
    background-color: #111827;
}

/* ── Message Box ───────────────────────────────────────── */
QMessageBox {
    background-color: #111827;
    color: #e2e8f0;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ── List Widget ──────────────────────────────────────── */
QListWidget {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    outline: none;
}

QListWidget::item {
    border-radius: 6px;
    padding: 6px;
}

QListWidget::item:selected {
    background-color: #14532d;
    color: #4ade80;
}

QListWidget::item:hover {
    background-color: #1e293b;
}

/* ── Toolbar ────────────────────────────────────────────── */
QToolBar {
    background-color: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 4px 8px;
    spacing: 4px;
}

/* ── Separator ─────────────────────────────────────────── */
#HSep {
    background-color: #1e293b;
    max-height: 1px;
    min-height: 1px;
}

/* ── Star / Favourite Button ─────────────────────────────── */
QPushButton#StarBtn {
    background-color: transparent;
    border: none;
    border-radius: 5px;
    font-size: 17px;
    padding: 1px 3px;
    color: #64748b;
}

QPushButton#StarBtn:hover {
    color: #fbbf24;
    background-color: rgba(251, 191, 36, 0.10);
    border: none;
}

QPushButton#StarBtn[active="true"] {
    color: #fbbf24;
}
"""
