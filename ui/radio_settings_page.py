from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.radio_manager import RadioManager
from ui.styles import PALETTE


class RadioSettingsPage(QWidget):
    def __init__(self, manager: RadioManager, music_target_folder: str, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._music_target_folder = music_target_folder
        self._build_ui()
        self._load_stations()
        self._refresh_linked_music_label()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel("Radio Settings")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel("Manage internet radio stations and local in-game music library")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(subtitle)

        internet_group = QGroupBox("Internet Radio")
        internet_layout = QVBoxLayout(internet_group)
        internet_layout.setSpacing(10)

        self._stations_list = QListWidget()
        self._stations_list.setMinimumHeight(220)
        self._stations_list.setStyleSheet(
            f"QListWidget {{ background-color: {PALETTE['surface']}; border: 1px solid {PALETTE['border']}; }}"
        )
        internet_layout.addWidget(self._stations_list)

        self._station_input = QLineEdit()
        self._station_input.setPlaceholderText("Enter stream URL (.mp3, .aac, .m3u, .pls)")
        self._station_input.setObjectName("SearchBar")
        internet_layout.addWidget(self._station_input)

        station_btns = QHBoxLayout()
        self._add_station_btn = QPushButton("Add Station")
        self._add_station_btn.setObjectName("PrimaryBtn")
        self._add_station_btn.setStyleSheet(
            f"QPushButton#PrimaryBtn {{ background-color: {PALETTE['primary']}; }}"
            f"QPushButton#PrimaryBtn:hover {{ background-color: {PALETTE['primary_hover']}; }}"
        )
        self._add_station_btn.clicked.connect(self._on_add_station)
        station_btns.addWidget(self._add_station_btn)

        self._remove_station_btn = QPushButton("Remove Selected")
        self._remove_station_btn.setObjectName("DangerBtn")
        self._remove_station_btn.clicked.connect(self._on_remove_station)
        station_btns.addWidget(self._remove_station_btn)

        station_btns.addStretch(1)
        internet_layout.addLayout(station_btns)

        local_group = QGroupBox("Local Music Library")
        local_layout = QVBoxLayout(local_group)
        local_layout.setSpacing(10)

        self._linked_folder_label = QLabel("No folder linked")
        self._linked_folder_label.setWordWrap(True)
        self._linked_folder_label.setStyleSheet(f"color: {PALETTE['muted']};")
        local_layout.addWidget(self._linked_folder_label)

        self._select_folder_btn = QPushButton("Select Music Folder")
        self._select_folder_btn.setObjectName("PrimaryBtn")
        self._select_folder_btn.setStyleSheet(
            f"QPushButton#PrimaryBtn {{ background-color: {PALETTE['primary']}; }}"
            f"QPushButton#PrimaryBtn:hover {{ background-color: {PALETTE['primary_hover']}; }}"
        )
        self._select_folder_btn.clicked.connect(self._on_select_music_folder)
        local_layout.addWidget(self._select_folder_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        root.addWidget(internet_group)
        root.addWidget(local_group)
        root.addStretch(1)

    def _load_stations(self):
        self._stations_list.clear()
        for url in self._manager.get_web_stations():
            self._stations_list.addItem(url)

    def _on_add_station(self):
        url = self._station_input.text().strip()
        if not url:
            QMessageBox.information(self, "Add Station", "Please enter a stream URL.")
            return

        if self._manager.add_web_station(url):
            self._station_input.clear()
            self._load_stations()
        else:
            QMessageBox.warning(self, "Add Station", "Station was not added (empty or already exists).")

    def _on_remove_station(self):
        item = self._stations_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Remove Station", "Select a station first.")
            return

        if self._manager.remove_web_station(item.text().strip()):
            self._load_stations()
        else:
            QMessageBox.warning(self, "Remove Station", "Failed to remove selected station.")

    def _refresh_linked_music_label(self):
        linked = self._manager.get_linked_music_folder(self._music_target_folder)
        if linked:
            self._linked_folder_label.setText(f"Linked folder: {linked}")
        else:
            self._linked_folder_label.setText("No folder linked")

    def _on_select_music_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Local Music Folder",
            "",
        )
        if not folder:
            return

        ok, message = self._manager.link_local_music_folder(folder, self._music_target_folder)
        if ok:
            self._refresh_linked_music_label()
            QMessageBox.information(self, "Local Music", "Music folder linked successfully.")
        else:
            QMessageBox.warning(self, "Local Music", message)
