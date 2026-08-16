from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.radio_browser import RadioBrowser
from core.radio_manager import RadioManager


class StationSearchWorker(QThread):
    """Fetch one page of stations without blocking the UI."""

    finished_ok = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, browser: RadioBrowser, query: str, page: int):
        super().__init__()
        self._browser = browser
        self._query = query
        self._page = page

    def run(self):
        try:
            self.finished_ok.emit(self._browser.search(self._query, page=self._page))
        except Exception as exc:  # network/parse failures are reported in the UI
            self.failed.emit(str(exc))


class RadioSettingsPage(QWidget):
    def __init__(self, manager: RadioManager, music_target_folder: str, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._music_target_folder = music_target_folder
        self._browser = RadioBrowser()
        self._worker: StationSearchWorker | None = None
        self._page = 0
        self._results: list[dict[str, Any]] = []
        self._build_ui()
        self._load_stations()
        self._refresh_linked_music_label()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        title = QLabel("Radio")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel("Browse online stations, keep your own list, and link local music")
        subtitle.setObjectName("PageSubtitle")
        root.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addWidget(self._build_browse_group(), stretch=1)
        columns.addWidget(self._build_mine_group(), stretch=1)
        root.addLayout(columns, stretch=1)

        root.addWidget(self._build_local_group())

    def _build_browse_group(self) -> QGroupBox:
        group = QGroupBox("Browse stations")
        lay = QVBoxLayout(group)
        lay.setSpacing(10)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._search_input = QLineEdit()
        self._search_input.setObjectName("SearchBar")
        self._search_input.setPlaceholderText("Search by name, e.g. rock, jazz, SWR3…")
        self._search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self._search_input, stretch=1)

        self._search_btn = QPushButton("Search")
        self._search_btn.setObjectName("ToolBtn")
        self._search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self._search_btn)
        lay.addLayout(search_row)

        self._results_list = QListWidget()
        self._results_list.setMinimumHeight(240)
        self._results_list.itemDoubleClicked.connect(lambda _: self._on_add_selected_result())
        lay.addWidget(self._results_list, stretch=1)

        nav = QHBoxLayout()
        nav.setSpacing(8)
        self._prev_btn = QPushButton("‹")
        self._prev_btn.setObjectName("ToolBtn")
        self._prev_btn.setFixedWidth(38)
        self._prev_btn.setToolTip("Previous page")
        self._prev_btn.clicked.connect(lambda: self._go_page(self._page - 1))
        nav.addWidget(self._prev_btn)

        self._page_lbl = QLabel("—")
        self._page_lbl.setObjectName("PageSubtitle")
        self._page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self._page_lbl, stretch=1)

        self._next_btn = QPushButton("›")
        self._next_btn.setObjectName("ToolBtn")
        self._next_btn.setFixedWidth(38)
        self._next_btn.setToolTip("Next page")
        self._next_btn.clicked.connect(lambda: self._go_page(self._page + 1))
        nav.addWidget(self._next_btn)
        lay.addLayout(nav)

        self._add_result_btn = QPushButton("Add to my stations  →")
        self._add_result_btn.setObjectName("PrimaryBtn")
        self._add_result_btn.clicked.connect(self._on_add_selected_result)
        lay.addWidget(self._add_result_btn)

        return group

    def _build_mine_group(self) -> QGroupBox:
        group = QGroupBox("My stations")
        lay = QVBoxLayout(group)
        lay.setSpacing(10)

        self._stations_list = QListWidget()
        self._stations_list.setMinimumHeight(240)
        lay.addWidget(self._stations_list, stretch=1)

        self._station_input = QLineEdit()
        self._station_input.setObjectName("SearchBar")
        self._station_input.setPlaceholderText("Or paste a stream URL (.mp3, .aac, .m3u, .pls)")
        self._station_input.returnPressed.connect(self._on_add_station)
        lay.addWidget(self._station_input)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        self._add_station_btn = QPushButton("Add URL")
        self._add_station_btn.setObjectName("ToolBtn")
        self._add_station_btn.clicked.connect(self._on_add_station)
        btns.addWidget(self._add_station_btn)

        self._remove_station_btn = QPushButton("Remove selected")
        self._remove_station_btn.setObjectName("DangerBtn")
        self._remove_station_btn.clicked.connect(self._on_remove_station)
        btns.addWidget(self._remove_station_btn)
        btns.addStretch(1)
        lay.addLayout(btns)

        return group

    def _build_local_group(self) -> QGroupBox:
        group = QGroupBox("Local music")
        lay = QHBoxLayout(group)
        lay.setSpacing(12)

        self._linked_folder_label = QLabel("No folder linked")
        self._linked_folder_label.setWordWrap(True)
        self._linked_folder_label.setObjectName("PageSubtitle")
        lay.addWidget(self._linked_folder_label, stretch=1)

        self._select_folder_btn = QPushButton("Select music folder")
        self._select_folder_btn.setObjectName("ToolBtn")
        self._select_folder_btn.clicked.connect(self._on_select_music_folder)
        lay.addWidget(self._select_folder_btn)

        return group

    # ── Browsing ─────────────────────────────────────────────────────────────
    def _on_search(self):
        self._go_page(0)

    def _go_page(self, page: int):
        if page < 0 or (self._worker is not None and self._worker.isRunning()):
            return
        self._page = page
        self._set_browsing(True)
        self._page_lbl.setText(f"Loading page {page + 1}…")

        self._worker = StationSearchWorker(self._browser, self._search_input.text(), page)
        self._worker.finished_ok.connect(self._on_results)
        self._worker.failed.connect(self._on_search_failed)
        self._worker.finished.connect(lambda: self._set_browsing(False))
        self._worker.start()

    def _set_browsing(self, busy: bool):
        for btn in (self._search_btn, self._prev_btn, self._next_btn, self._add_result_btn):
            btn.setEnabled(not busy)
        if not busy:
            self._prev_btn.setEnabled(self._page > 0)
            self._next_btn.setEnabled(len(self._results) >= RadioBrowser.PAGE_SIZE)

    def _on_results(self, stations: list):
        self._results = stations
        self._results_list.clear()
        for station in stations:
            meta = " · ".join(
                p for p in (
                    station.get("country") or "",
                    station.get("codec") or "",
                    f"{station['bitrate']}kbps" if station.get("bitrate") else "",
                ) if p
            )
            item = QListWidgetItem(f"{station['name']}\n{meta}" if meta else station["name"])
            item.setToolTip(station["url"])
            self._results_list.addItem(item)

        if not stations:
            self._page_lbl.setText("No stations found" if self._page == 0 else f"Page {self._page + 1} — empty")
        else:
            self._page_lbl.setText(f"Page {self._page + 1}")

    def _on_search_failed(self, message: str):
        self._results = []
        self._results_list.clear()
        self._page_lbl.setText("Search failed")
        QMessageBox.warning(
            self,
            "Radio search",
            f"Could not reach the station directory.\n\n{message}",
        )

    def _on_add_selected_result(self):
        row = self._results_list.currentRow()
        if row < 0 or row >= len(self._results):
            QMessageBox.information(self, "Add station", "Select a station from the list first.")
            return

        station = self._results[row]
        if self._manager.add_web_station(station["url"], station["name"]):
            self._load_stations()
        else:
            QMessageBox.information(self, "Add station", "That station is already in your list.")

    # ── My stations ──────────────────────────────────────────────────────────
    def _load_stations(self):
        self._stations_list.clear()
        stations = self._manager.get_stations()
        for station in stations:
            label = f"{station['name']}\n{station['url']}" if station["name"] else station["url"]
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, station["url"])
            item.setToolTip(station["url"])
            self._stations_list.addItem(item)
        self._remove_station_btn.setEnabled(bool(stations))

    def _on_add_station(self):
        url = self._station_input.text().strip()
        if not url:
            QMessageBox.information(self, "Add station", "Please enter a stream URL.")
            return

        if self._manager.add_web_station(url):
            self._station_input.clear()
            self._load_stations()
        else:
            QMessageBox.warning(self, "Add station", "Station was not added (empty or already exists).")

    def _on_remove_station(self):
        item = self._stations_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Remove station", "Select a station first.")
            return

        url = item.data(Qt.ItemDataRole.UserRole) or item.text().strip()
        if self._manager.remove_web_station(url):
            self._load_stations()
        else:
            QMessageBox.warning(self, "Remove station", "Failed to remove selected station.")

    # ── Local music ──────────────────────────────────────────────────────────
    def _refresh_linked_music_label(self):
        linked = self._manager.get_linked_music_folder(self._music_target_folder)
        self._linked_folder_label.setText(
            f"Linked folder: {linked}" if linked else "No folder linked"
        )

    def _on_select_music_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Local Music Folder", "")
        if not folder:
            return

        ok, message = self._manager.link_local_music_folder(folder, self._music_target_folder)
        if ok:
            self._refresh_linked_music_label()
            QMessageBox.information(self, "Local music", "Music folder linked successfully.")
        else:
            QMessageBox.warning(self, "Local music", message)

    def closeEvent(self, event):  # type: ignore[override]
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.quit()
            worker.wait(3000)
        super().closeEvent(event)
