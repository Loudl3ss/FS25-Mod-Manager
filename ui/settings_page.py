"""Game settings page."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.settings_manager import (
    DIFF_MAP, FUEL_MAP, REALISM_MAP, GameSettings, SettingsManager,
)
from ui.widgets import HSeparator


class SettingsPage(QWidget):
    def __init__(self, manager: SettingsManager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._settings: GameSettings | None = None
        self._build_ui()
        self._load()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        ttl_col = QVBoxLayout()
        ttl_col.setSpacing(2)
        ttl = QLabel("🎛 Game Settings")
        ttl.setObjectName("PageTitle")
        ttl_col.addWidget(ttl)
        sub = QLabel("Tweak difficulty, realism and economy settings")
        sub.setObjectName("PageSubtitle")
        ttl_col.addWidget(sub)
        hdr.addLayout(ttl_col, stretch=1)
        root.addLayout(hdr)

        root.addWidget(HSeparator())

        # Scrollable area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 12, 0)
        content_lay.setSpacing(16)

        # ── Difficulty group ──────────────────────────────────────────────────
        diff_grp = QGroupBox("Difficulty")
        diff_form = QFormLayout(diff_grp)
        diff_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        diff_form.setSpacing(10)

        self._cb_diff = self._make_combo(DIFF_MAP)
        diff_form.addRow("Game Difficulty:", self._cb_diff)

        self._cb_econ = self._make_combo(DIFF_MAP)
        diff_form.addRow("Economy Difficulty:", self._cb_econ)

        content_lay.addWidget(diff_grp)

        # ── Realism group ─────────────────────────────────────────────────────
        real_grp = QGroupBox("Vehicle & Realism")
        real_form = QFormLayout(real_grp)
        real_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        real_form.setSpacing(10)

        self._cb_fuel = self._make_combo(FUEL_MAP)
        real_form.addRow("Fuel Usage:", self._cb_fuel)

        self._cb_dirt = self._make_combo(REALISM_MAP)
        real_form.addRow("Dirt Interval:", self._cb_dirt)

        self._cb_damage = self._make_combo(REALISM_MAP)
        real_form.addRow("Vehicle Damage:", self._cb_damage)

        content_lay.addWidget(real_grp)

        # ── Economy group ─────────────────────────────────────────────────────
        econ_grp = QGroupBox("Economy")
        econ_form = QFormLayout(econ_grp)
        econ_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        econ_form.setSpacing(10)

        self._spin_interest = QDoubleSpinBox()
        self._spin_interest.setRange(0.0, 100.0)
        self._spin_interest.setSingleStep(0.5)
        self._spin_interest.setSuffix(" %")
        econ_form.addRow("Loan Interest Rate:", self._spin_interest)

        self._spin_price = QDoubleSpinBox()
        self._spin_price.setRange(0.0, 1.0)
        self._spin_price.setSingleStep(0.05)
        self._spin_price.setDecimals(2)
        econ_form.addRow("Price Change Range:", self._spin_price)

        content_lay.addWidget(econ_grp)

        # ── Toggles group ────────────────────────────────────────────────────
        tog_grp = QGroupBox("Farm Conditions")
        tog_form = QFormLayout(tog_grp)
        tog_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        tog_form.setSpacing(10)

        self._chk_plow = QCheckBox("Plowing Required")
        tog_form.addRow(self._chk_plow)

        self._chk_stones = QCheckBox("Stones Enabled")
        tog_form.addRow(self._chk_stones)

        self._chk_weeds = QCheckBox("Weeds Enabled")
        tog_form.addRow(self._chk_weeds)

        self._chk_lime = QCheckBox("Lime Required")
        tog_form.addRow(self._chk_lime)

        self._chk_snow = QCheckBox("Snow Enabled")
        tog_form.addRow(self._chk_snow)

        content_lay.addWidget(tog_grp)
        content_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── Bottom action buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        btn_reset = QPushButton("↩ Reset to Defaults")
        btn_reset.setObjectName("ToolBtn")
        btn_reset.clicked.connect(self._reset)
        btn_row.addWidget(btn_reset)

        btn_save = QPushButton("💾 Save Settings")
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        root.addLayout(btn_row)

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _make_combo(mapping: dict) -> QComboBox:
        cb = QComboBox()
        for k, v in mapping.items():
            cb.addItem(v, k)
        return cb

    def _set_combo(self, cb: QComboBox, value: int):
        for i in range(cb.count()):
            if cb.itemData(i) == value:
                cb.setCurrentIndex(i)
                return

    # ── Load / Save ────────────────────────────────────────────────────────────
    def _load(self, settings: GameSettings | None = None):
        s = settings or self._manager.load()
        self._settings = s

        self._set_combo(self._cb_diff, s.difficulty)
        self._set_combo(self._cb_econ, s.economy_difficulty)
        self._set_combo(self._cb_fuel, s.fuel_usage)
        self._set_combo(self._cb_dirt, s.dirt_interval)
        self._set_combo(self._cb_damage, s.vehicle_damage_age)

        self._spin_interest.setValue(s.loan_interest_rate)
        self._spin_price.setValue(s.price_change_range)

        self._chk_plow.setChecked(s.plowing_required)
        self._chk_stones.setChecked(s.stones_enabled)
        self._chk_weeds.setChecked(s.weeds_enabled)
        self._chk_lime.setChecked(s.lime_required)
        self._chk_snow.setChecked(s.snow_enabled)

    def _collect(self) -> GameSettings:
        s = GameSettings()
        s._path = self._settings._path if self._settings else ""
        s.difficulty = self._cb_diff.currentData()
        s.economy_difficulty = self._cb_econ.currentData()
        s.fuel_usage = self._cb_fuel.currentData()
        s.dirt_interval = self._cb_dirt.currentData()
        s.vehicle_damage_age = self._cb_damage.currentData()
        s.loan_interest_rate = self._spin_interest.value()
        s.price_change_range = self._spin_price.value()
        s.plowing_required = self._chk_plow.isChecked()
        s.stones_enabled = self._chk_stones.isChecked()
        s.weeds_enabled = self._chk_weeds.isChecked()
        s.lime_required = self._chk_lime.isChecked()
        s.snow_enabled = self._chk_snow.isChecked()
        return s

    def _save(self):
        s = self._collect()
        if not s._path:
            QMessageBox.warning(
                self, "No Settings File",
                "gameSettings.xml not found in your FS25 folder.\n"
                "Launch the game once to create it.",
            )
            return
        if self._manager.save(s):
            QMessageBox.information(self, "Saved", "Settings saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")

    def _reset(self):
        reply = QMessageBox.question(
            self, "Reset Defaults",
            "Reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            defaults = GameSettings(_path=self._settings._path if self._settings else "")
            self._load(defaults)
