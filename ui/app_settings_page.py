"""Global app settings page."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, QTimer, QSize, Qt
from PyQt6.QtGui import QIcon

from core.app_config import AppConfigManager
from ui.widgets import HSeparator
from ui.assets import Icons


class AppSettingsPage(QWidget):
    """Page for configuring application folder paths."""

    rescan_requested = pyqtSignal()
    backup_folder_changed = pyqtSignal(str)
    manager_cache_root_changed = pyqtSignal(str)

    def __init__(self, app_config_manager: AppConfigManager, parent=None):
        super().__init__(parent)
        self._manager = app_config_manager
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

        # Mods Folder
        self._add_path_setting(
            root, 
            "MODS FOLDER", 
            self._manager.config.mods_folder,
            self._on_mods_folder_selected,
            "select_mods_folder"
        )

        # Savedgames Folder
        self._add_path_setting(
            root,
            "SAVEDGAMES FOLDER",
            self._manager.config.savedgames_folder,
            self._on_savedgames_folder_selected,
            "select_savedgames_folder"
        )

        # Backup Folder
        self._add_path_setting(
            root,
            "BACKUP FOLDER",
            self._manager.config.backup_folder,
            self._on_backup_folder_selected,
            "select_backup_folder"
        )

        # FS25 Mod Manager cache root folder
        self._add_path_setting(
            root,
            "FS25 MOD MANAGER CACHE ROOT",
            self._manager.config.manager_cache_root,
            self._on_manager_cache_root_selected,
            "select_manager_cache_root"
        )

        # Game Install Path
        self._add_path_setting(
            root,
            "GAME INSTALL PATH",
            self._manager.config.game_install_path,
            self._on_game_install_path_selected,
            "select_game_path"
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

    def _add_path_setting(self, parent_layout, label_text: str, current_path: str, callback, setting_id: str):
        """Add a path setting row with browse button."""
        section_title = QLabel(label_text)
        section_title.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 12px;")
        parent_layout.addWidget(section_title)

        row = QFrame()
        row.setProperty("class", "PathSettingRow")
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        r_lay = QHBoxLayout(row)
        r_lay.setContentsMargins(16, 12, 16, 12)
        r_lay.setSpacing(12)

        # Path label
        path_lbl = QLabel(current_path if current_path else "No path selected")
        path_lbl.setObjectName("PathLabel")
        path_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        path_lbl.setWordWrap(True)
        setattr(self, f"{setting_id}_label", path_lbl)
        r_lay.addWidget(path_lbl, stretch=1)

        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("ToolBtn")
        browse_btn.setFixedSize(100, 36)
        browse_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_btn.clicked.connect(callback)
        r_lay.addWidget(browse_btn)

        parent_layout.addWidget(row)
        parent_layout.addSpacing(12)

    def _on_mods_folder_selected(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Mods Folder",
            self._manager.config.mods_folder or ""
        )
        if folder:
            self._manager.config.mods_folder = folder
            self._manager.save()
            self.select_mods_folder_label.setText(folder)

    def _on_savedgames_folder_selected(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Savedgames Folder",
            self._manager.config.savedgames_folder or ""
        )
        if folder:
            self._manager.config.savedgames_folder = folder
            self._manager.save()
            self.select_savedgames_folder_label.setText(folder)

    def _on_game_install_path_selected(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Game Install Path",
            self._manager.config.game_install_path or ""
        )
        if folder:
            self._manager.config.game_install_path = folder
            self._manager.save()
            self.select_game_path_label.setText(folder)

    def _on_backup_folder_selected(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
            self._manager.config.backup_folder or self._manager.config.savedgames_folder or ""
        )
        if folder:
            self._manager.config.backup_folder = folder
            self._manager.save()
            self.select_backup_folder_label.setText(folder)
            self.backup_folder_changed.emit(folder)

    def _on_manager_cache_root_selected(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select FS25 Mod Manager Cache Root",
            self._manager.config.manager_cache_root or self._manager.config.game_install_path or ""
        )
        if folder:
            self._manager.config.manager_cache_root = folder
            self._manager.save()
            self.select_manager_cache_root_label.setText(folder)
            self.manager_cache_root_changed.emit(folder)

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
