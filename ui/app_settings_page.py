"""Global app settings page."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from core.app_config import AppConfigManager
from ui.widgets import HSeparator, ToggleSwitch


class AppSettingsPage(QWidget):
    """Page for configuring application-level behavior."""

    def __init__(self, app_config_manager: AppConfigManager, parent=None):
        super().__init__(parent)
        self._manager = app_config_manager
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Application Settings")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel("Configure how the Mod Manager filters library content.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        root.addWidget(HSeparator())

        section_title = QLabel("MOD MANAGER FILTERING")
        section_title.setObjectName("DashboardSectionLabel")
        root.addWidget(section_title)

        def add_setting_row(title: str, desc: str, initial_state: bool, callback):
            row = QFrame()
            row.setProperty("class", "SettingsRow")
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(16, 12, 16, 12)
            r_lay.setSpacing(12)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            lbl = QLabel(title)
            lbl.setObjectName("ModTitle")
            d_lbl = QLabel(desc)
            d_lbl.setObjectName("ModMeta")
            d_lbl.setWordWrap(True)
            text_col.addWidget(lbl)
            text_col.addWidget(d_lbl)

            r_lay.addLayout(text_col, stretch=1)

            toggle = ToggleSwitch(checked=initial_state)
            toggle.toggled.connect(lambda v: self._handle_toggle(callback, v))
            r_lay.addWidget(toggle, alignment=Qt.AlignmentFlag.AlignVCenter)

            root.addWidget(row)

        cfg = self._manager.config
        add_setting_row(
            "Show Favorites in All Mods",
            "Shows favorited mods in both Favorites and All Mods views.",
            cfg.show_favorites_in_all_mods,
            self._set_fav_in_all,
        )
        add_setting_row(
            "Include Maps in All Mods",
            "Includes map mods in the All Mods library list.",
            cfg.include_maps_in_all_mods,
            self._set_maps_in_all,
        )
        add_setting_row(
            "Strict Map Filtering",
            "Only show map mods inside the Maps library page.",
            cfg.strict_map_filtering,
            self._set_strict_maps,
        )

        root.addStretch()

    def _handle_toggle(self, func, value: bool):
        func(value)
        self._manager.save()

    def _set_fav_in_all(self, val: bool):
        self._manager.config.show_favorites_in_all_mods = val

    def _set_maps_in_all(self, val: bool):
        self._manager.config.include_maps_in_all_mods = val

    def _set_strict_maps(self, val: bool):
        self._manager.config.strict_map_filtering = val
