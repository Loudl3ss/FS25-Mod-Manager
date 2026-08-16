"""Global QSS dark theme for FS25 Manager."""

PALETTE = {
    "primary": "#3f7d51",
    "primary_hover": "#356a45",
    "danger": "#5c2626",
    "surface": "#161a21",
    "border": "#2b313b",
    "text": "#d5dbe3",
    "text_dim": "#8b94a1",
    "muted": "#7d8694",
}

DARK_THEME = """
/* ── Global ─────────────────────────────────────────── */
QWidget {
    background: transparent;
    color: #d5dbe3;
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}

/* Subtilus gylis: beveik juodas fonas su vienu pašviesėjimu viršuje kairėje.
   Qt QSS neturi backdrop-filter, todėl "stiklas" kuriamas permatomumu virs
   sio gradiento, ne blur'u. */
QMainWindow {
    background: qradialgradient(cx: 0.22, cy: 0.08, radius: 1.1,
                                fx: 0.22, fy: 0.08,
                                stop: 0 #171d26,
                                stop: 0.55 #0f1319,
                                stop: 1 #0a0d11);
}

QDialog {
    background: qradialgradient(cx: 0.3, cy: 0.0, radius: 1.2,
                                fx: 0.3, fy: 0.0,
                                stop: 0 #171d26,
                                stop: 1 #0a0d11);
}

/* ── Sidebar ─────────────────────────────────────────── */
#Sidebar {
    background-color: rgba(255, 255, 255, 0.022);
    border-right: 1px solid rgba(255, 255, 255, 0.055);
    min-width: 224px;
    max-width: 224px;
}

#SidebarLogo {
    font-size: 26px;
    font-weight: 700;
    color: #e5e7eb;
    padding: 10px 12px 2px 12px;
    letter-spacing: 0.5px;
}

#SidebarSubtitle {
    font-size: 10px;
    color: #7d8694;
    padding: 0 16px 8px 16px;
    letter-spacing: 2px;
}

QLabel#SidebarSection {
    color: #7d8694;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.8px;
    padding: 5px 0 1px 12px;
}

QPushButton#NavBtn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    text-align: left;
    padding: 6px 12px;
    font-size: 13px;
    color: #8b94a1;
    margin: 0px 14px 0px 10px;
}

QPushButton#NavBtn:hover {
    background-color: #161a21;
    border-color: #2b313b;
    color: #e6eaf0;
}

QPushButton#NavBtn:pressed {
    background-color: #0e1116;
    border-color: #414b59;
}

QPushButton#NavBtn[active="true"] {
    background-color: #1a2b20;
    border-color: #3a5c46;
    color: #7cb98d;
    font-weight: 600;
}

QPushButton#NavBtn[active="false"] {
    margin: 0px 14px 0px 10px;
}

/* ── Content Area ────────────────────────────────────── */
#ContentArea {
    background: transparent;
}

#PageTitle {
    font-size: 24px;
    font-weight: 650;
    color: #eef1f6;
    letter-spacing: 0.4px;
    padding: 4px 0;
}

#PageSubtitle {
    font-size: 12.5px;
    color: #7d8694;
    letter-spacing: 0.1px;
}

/* ── Stat Cards ─────────────────────────────────────── */
#card_installed, #card_favourited, #card_maps, #card_disk, #card_saves, #card_backups {
    background-color: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.065);
    border-bottom: 2px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
}



#card_installed #StatValue, #card_installed #StatIcon { color: #5a9e6b; font-weight: bold; font-size: 15pt; border: none; background: transparent; }
#card_favourited #StatValue, #card_favourited #StatIcon { color: #b89b5b; font-weight: bold; font-size: 15pt; border: none; background: transparent; }
#card_maps #StatValue, #card_maps #StatIcon { color: #5b87b8; font-weight: bold; font-size: 15pt; border: none; background: transparent; }
#card_disk #StatValue, #card_disk #StatIcon { color: #8f6ba8; font-weight: bold; font-size: 15pt; border: none; background: transparent; }
#card_saves #StatValue, #card_saves #StatIcon { color: #5a9e6b; font-weight: bold; font-size: 15pt; border: none; background: transparent; }
#card_backups #StatValue, #card_backups #StatIcon { color: #5b87b8; font-weight: bold; font-size: 15pt; border: none; background: transparent; }

#StatCategory {
    color: #8b94a1;
    font-size: 11px;
    font-weight: bold;
    background: transparent;
    border: none;
}

#StatValue {
    font-size: 21px;
    font-weight: 700;
    color: #5a9e6b;
}

#StatLabel {
    font-size: 11px;
    color: #7d8694;
    letter-spacing: 1px;
}

/* ── Search / Filter ─────────────────────────────────── */
QLineEdit#SearchBar {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 13px;
    color: #d5dbe3;
    selection-background-color: #5a9e6b;
    selection-color: #000;
}

QLineEdit#SearchBar:focus {
    border-color: #5a9e6b;
}

/* ── Mod / Save Cards ─────────────────────────────────── */
#ModCard {
    background-color: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.065);
    border-radius: 10px;
    padding: 14px 16px;
    margin: 4px 5px;
}

#ModCard:hover {
    background-color: rgba(255, 255, 255, 0.055);
    border-color: rgba(255, 255, 255, 0.12);
}

#ModCard[selected="true"], #ModCard[selectedForGame="true"] {
    background-color: rgba(90, 158, 107, 0.13);
    border-color: rgba(122, 194, 141, 0.45);
}

#ModTitle {
    font-size: 13px;
    font-weight: 600;
    color: #e6eaf0;
}

#ModAuthor {
    font-size: 11px;
    color: #8b94a1;
}

#ModMeta {
    font-size: 11px;
    color: #7d8694;
}

/* ── Badges ──────────────────────────────────────────── */
#BadgeEnabled {
    background-color: #1d2b22;
    color: #5a9e6b;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

#BadgeDisabled {
    background-color: #2a1a1a;
    color: #c98787;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {
    background-color: #161a21;
    border: 1px solid #2b313b;
    border-radius: 4px;
    padding: 6px 14px;
    color: #d5dbe3;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1c222b;
    border-color: #414b59;
    color: #e6eaf0;
}

QPushButton:pressed {
    background-color: #10141a;
    border-color: #5a9e6b;
    padding-top: 7px;
    padding-bottom: 5px;
}

QPushButton:disabled {
    background-color: #12161c;
    border-color: #232830;
    color: #6a7280;
}

QPushButton#PrimaryBtn {
    background-color: #3f7d51;
    border: 1px solid #5a9e6b;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 4px;
}

QPushButton#PrimaryBtn:hover {
    background-color: #4a8c5c;
    border-color: #6bb07d;
}

QPushButton#PrimaryBtn:pressed {
    background-color: #2c5a3b;
    border-color: #4a8c5c;
    padding-top: 9px;
    padding-bottom: 7px;
}

QPushButton#PrimaryBtn:disabled {
    background-color: #1e2a23;
    border-color: #2b3a31;
    color: #6b7a70;
}

QPushButton#DangerBtn {
    background-color: #5c2626;
    border: 1px solid #8a4a4a;
    color: #e0b4b4;
}

QPushButton#DangerBtn:hover {
    background-color: #7e3232;
    border-color: #b06a6a;
}

QPushButton#DangerBtn:pressed {
    background-color: #4d1f1f;
    border-color: #8a4a4a;
}

QPushButton#DangerBtn:disabled {
    background-color: #23191a;
    border-color: #332626;
    color: #7a6060;
}

QPushButton#SuccessBtn {
    background-color: #1d2b22;
    border: 1px solid #5a9e6b;
    color: #5a9e6b;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
}

QPushButton#SuccessBtn:hover {
    background-color: #23402e;
    border-color: #6bb07d;
    color: #9ccfa9;
}

QPushButton#SuccessBtn:pressed {
    background-color: #16261c;
    border-color: #4a8c5c;
}

QPushButton#ToolBtn {
    background-color: transparent;
    border: 1px solid #2b313b;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
    color: #8b94a1;
}

QPushButton#ToolBtn:hover {
    background-color: #1c222b;
    color: #e6eaf0;
    border-color: #414b59;
}

QPushButton#ToolBtn:pressed {
    background-color: #10141a;
    border-color: #5a9e6b;
}

QPushButton#ToolBtn:disabled {
    color: #6a7280;
    border-color: #232830;
}

QPushButton#LaunchBtn {
    background-color: #4a8c5c;
    color: #0a0d11;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 14px;
    border-radius: 4px;
    border: 1px solid #4a8c5c;
    margin: 6px 14px 6px 10px;
}

QPushButton#LaunchBtn:hover {
    background-color: #3f7a4f;
    border-color: #3f7a4f;
}

QPushButton#LaunchBtn:pressed {
    background-color: #356a45;
    border-color: #356a45;
}

QFrame#DetailThumb {
    background: transparent;
    border: 1px dashed rgba(255, 255, 255, 0.10);
    border-radius: 10px;
}

QFrame#DetailThumb[filled="true"] {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

QFrame#SaveRow {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.055);
    border-radius: 8px;
}

QFrame#SaveRow:hover {
    background-color: rgba(255, 255, 255, 0.055);
    border-color: rgba(255, 255, 255, 0.11);
}

QLabel#EmptyState {
    color: #8b94a1;
    font-size: 14px;
    padding: 48px 24px;
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
    border-radius: 4px;
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
    background-color: #3f7d51;
    border: 1px solid #5a9e6b;
    border-radius: 4px;
    color: #ffffff;
    font-weight: 700;
    padding: 8px 18px;
    min-width: 92px;
}

QPushButton#WizardNavPrimaryBtn:hover {
    background-color: #356a45;
    border-color: #6bb07d;
}

QPushButton#WizardNavPrimaryBtn:pressed {
    background-color: #2c5a3b;
}

/* ── Scrollbar ───────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.13);
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.22);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.13);
    border-radius: 4px;
    min-width: 30px;
}

/* ── Splitter ─────────────────────────────────────────── */
QSplitter::handle {
    background: #161a21;
    width: 2px;
}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 6px 10px;
    color: #d5dbe3;
    min-width: 140px;
}

QComboBox:hover {
    border-color: rgba(255, 255, 255, 0.16);
}

QComboBox:focus {
    border-color: rgba(122, 194, 141, 0.55);
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #161a21;
    border: 1px solid #2b313b;
    selection-background-color: #1d2b22;
    color: #d5dbe3;
    border-radius: 4px;
}

/* ── CheckBox ─────────────────────────────────────────── */
QCheckBox {
    color: #d5dbe3;
    spacing: 8px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 2px solid #2b313b;
    border-radius: 4px;
    background-color: #161a21;
}

QCheckBox::indicator:checked {
    background-color: #3f7d51;
    border-color: #5a9e6b;
    image: none;
}

QCheckBox::indicator:hover {
    border-color: #5a9e6b;
}

/* ── Double Spinbox ────────────────────────────────────── */
QDoubleSpinBox, QSpinBox {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 6px 10px;
    color: #d5dbe3;
}

QDoubleSpinBox:hover, QSpinBox:hover {
    border-color: rgba(255, 255, 255, 0.16);
}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #2b313b;
    border: none;
    border-radius: 3px;
    width: 16px;
}

/* ── GroupBox ─────────────────────────────────────────── */
QGroupBox {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 4px;
    margin-top: 14px;
    padding: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #8b94a1;
    letter-spacing: 1px;
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
    color: #d5dbe3;
}

/* ── Status Bar ────────────────────────────────────────── */
QStatusBar {
    background-color: #0b0e12;
    color: #7d8694;
    border-top: 1px solid #161a21;
    font-size: 11px;
}

/* ── Dialog ────────────────────────────────────────────── */
QDialog {
    background-color: #0e1116;
}

/* ── Message Box ───────────────────────────────────────── */
QMessageBox {
    background-color: #0e1116;
    color: #d5dbe3;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ── List Widget ──────────────────────────────────────── */
QListWidget {
    background-color: #0b0e12;
    border: 1px solid #161a21;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    border-radius: 4px;
    padding: 6px;
}

QListWidget::item:selected {
    background-color: #1d2b22;
    color: #5a9e6b;
}

QListWidget::item:hover {
    background-color: #161a21;
}

/* ── Toolbar ────────────────────────────────────────────── */
QToolBar {
    background-color: #0b0e12;
    border-bottom: 1px solid #161a21;
    padding: 4px 8px;
    spacing: 4px;
}

/* ── Separator ─────────────────────────────────────────── */
#HSep {
    background-color: #161a21;
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
    color: #7d8694;
}

QPushButton#StarBtn:hover {
    color: #d1a44e;
    background-color: rgba(251, 191, 36, 0.10);
    border: none;
}

QPushButton#StarBtn[active="true"] {
    color: #d1a44e;
}
"""
