"""Global app settings page."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from core.app_config import AppConfigManager
from ui.assets import Icons
from ui.widgets import BasePage, HSeparator, ToggleSwitch


class AppSettingsPage(BasePage):
    """Page for configuring application-level features like Mod Manager filtering behavior."""

    def __init__(self, app_config_manager: AppConfigManager, parent=None):
        super().__init__(parent, scrollable=True)
        self._manager = app_config_manager
        self._build_ui()

    def _build_ui(self):
        # Configure Header
        self.set_header("Application Settings", "Configure how the Mod Manager filters variables and handles lists.", Icons.APP_SETTINGS)

        # Body: Filtering Options
        section_title = QLabel("MOD MANAGER FILTERING")
        section_title.setProperty("class", "DashboardSectionLabel")
        self.content_layout.addWidget(section_title)

        def add_setting_row(title: str, desc: str, initial_state: bool, callback):
            row = QFrame()
            row.setProperty("class", "SettingsRow")
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(16, 16, 16, 16)

            text_col = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setProperty("class", "SettingsTitle")
            d_lbl = QLabel(desc)
            d_lbl.setProperty("class", "SettingsDesc")
            text_col.addWidget(lbl)
            text_col.addWidget(d_lbl)
            text_col.addStretch()

            r_lay.addLayout(text_col, stretch=1)

            toggle = ToggleSwitch(checked=initial_state)
            toggle.toggled.connect(lambda v: self._handle_toggle(callback, v))
            r_lay.addWidget(toggle)

            self.content_layout.addWidget(row)
            return toggle

        cfg = self._manager.config

        add_setting_row(
            "Show Favorites in 'All Mods' library",
            "If enabled, favorited mods will appear twice (in pinned top row and in the main list) on the dashboard.",
            cfg.show_favorites_in_all_mods,
            self._set_fav_in_all
        )

        add_setting_row(
            "Include Maps in 'All Mods' library",
            "If enabled, Map mods will be visible in the general Mods grid rather than hidden entirely to their own tab.",
            cfg.include_maps_in_all_mods,
            self._set_maps_in_all
        )

        add_setting_row(
            "Strict Map Filtering",
            "Forces Map mods to exclusively appear when the 'Maps' category/page is selected.",
            cfg.strict_map_filtering,
            self._set_strict_maps
        )

        self.content_layout.addStretch()

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _handle_toggle(self, func, value: bool):
        func(value)
        self._manager.save()

    def _set_fav_in_all(self, val: bool):
        self._manager.config.show_favorites_in_all_mods = val

    def _set_maps_in_all(self, val: bool):
        self._manager.config.include_maps_in_all_mods = val

    def _set_strict_maps(self, val: bool):
        self._manager.config.strict_map_filtering = val
