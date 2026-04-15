"""Global app settings page."""
from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, QTimer, QSize, Qt
from PyQt6.QtGui import QIcon

from core.app_config import AppConfigManager
from ui.widgets import HSeparator, PathSettingRow
from ui.assets import Icons


class AppSettingsPage(QWidget):
    """Page for configuring application folder paths."""

    rescan_requested = pyqtSignal()
    backup_folder_changed = pyqtSignal(str)
    manager_cache_root_changed = pyqtSignal(str)

    def __init__(self, app_config_manager: AppConfigManager, parent=None):
        super().__init__(parent)
        self._manager = app_config_manager
        self._path_rows: dict[str, PathSettingRow] = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel("Configure paths and preferences")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        root.addWidget(HSeparator())

        for spec in self._path_setting_specs():
            self._add_path_setting(
                parent_layout=root,
                label_text=spec["label_text"],
                config_key=spec["config_key"],
                dialog_title=spec["dialog_title"],
                fallback_keys=spec.get("fallback_keys", ()),
                change_signal=spec.get("change_signal"),
            )

        root.addStretch()

        # Bottom button bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self._save_rescan_btn = QPushButton("Save & Rescan")
        self._save_rescan_btn.setObjectName("PrimaryBtn")
        self._save_rescan_btn.setFixedSize(140, 36)
        self._save_rescan_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._save_rescan_btn.clicked.connect(self._on_save_and_rescan)
        btn_layout.addWidget(self._save_rescan_btn)

        root.addLayout(btn_layout)

        # Timer for reverting button state
        self._reset_button_timer = QTimer()
        self._reset_button_timer.setSingleShot(True)
        self._reset_button_timer.timeout.connect(self._reset_save_button)

    def _path_setting_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "label_text": "MODS FOLDER",
                "config_key": "mods_folder",
                "dialog_title": "Select Mods Folder",
            },
            {
                "label_text": "SAVEDGAMES FOLDER",
                "config_key": "savedgames_folder",
                "dialog_title": "Select Savedgames Folder",
            },
            {
                "label_text": "BACKUP FOLDER",
                "config_key": "backup_folder",
                "dialog_title": "Select Backup Folder",
                "fallback_keys": ("savedgames_folder",),
                "change_signal": self.backup_folder_changed,
            },
            {
                "label_text": "FS25 MOD MANAGER CACHE ROOT",
                "config_key": "manager_cache_root",
                "dialog_title": "Select FS25 Mod Manager Cache Root",
                "fallback_keys": ("game_install_path",),
                "change_signal": self.manager_cache_root_changed,
            },
            {
                "label_text": "GAME INSTALL PATH",
                "config_key": "game_install_path",
                "dialog_title": "Select Game Install Path",
            },
        ]

    def _add_path_setting(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
        config_key: str,
        dialog_title: str,
        fallback_keys: tuple[str, ...] = (),
        change_signal=None,
    ):
        """Add a path setting row with a generic browse callback."""
        section_title = QLabel(label_text)
        section_title.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 12px;")
        parent_layout.addWidget(section_title)

        current_path = getattr(self._manager.config, config_key, "") or ""
        row = PathSettingRow(current_path=current_path)
        self._path_rows[config_key] = row
        row.browse_requested.connect(
            lambda ck=config_key, dt=dialog_title, fk=fallback_keys, sig=change_signal: self._select_path(
                ck,
                dt,
                fk,
                sig,
            )
        )

        parent_layout.addWidget(row)
        parent_layout.addSpacing(12)

    def _select_path(
        self,
        config_key: str,
        dialog_title: str,
        fallback_keys: tuple[str, ...] = (),
        change_signal=None,
    ) -> None:
        start_dir = getattr(self._manager.config, config_key, "") or ""
        if not start_dir:
            for key in fallback_keys:
                start_dir = getattr(self._manager.config, key, "") or ""
                if start_dir:
                    break

        folder = QFileDialog.getExistingDirectory(
            self,
            dialog_title,
            start_dir,
        )
        if folder:
            setattr(self._manager.config, config_key, folder)
            self._manager.save()
            row = self._path_rows.get(config_key)
            if row is not None:
                row.set_path(folder)
            if change_signal is not None:
                change_signal.emit(folder)

    def _on_save_and_rescan(self):
        """Save configuration and request a rescan."""
        self._manager.save()
        
        # Show success feedback
        self._save_rescan_btn.setEnabled(False)
        self._save_rescan_btn.setText("Saved")
        self._save_rescan_btn.setIcon(Icons.get_qicon(Icons.SUCESFULL))
        self._save_rescan_btn.setIconSize(QSize(18, 18))
        
        # Emit rescan signal
        self.rescan_requested.emit()
        
        # Revert after 2 seconds
        self._reset_button_timer.start(2000)

    def _reset_save_button(self):
        """Reset the save button to its original state."""
        self._save_rescan_btn.setEnabled(True)
        self._save_rescan_btn.setText("Save & Rescan")
        self._save_rescan_btn.setIcon(QIcon())
