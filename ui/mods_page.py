"""Mods management page."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.mod_manager import ModInfo, ModManager
from core.thumbnail_loader import ThumbnailLoader
from ui.assets import Icons
from ui.favorite_grid import FavoriteModGrid
from ui.mod_grid import ModCard, ResponsiveModGrid
from ui.widgets import Badge, HSeparator, StatCard


# ─────────────────────────────────────────────────────────────────────────────
# Background loader
# ─────────────────────────────────────────────────────────────────────────────
class ModLoaderThread(QThread):
    loaded = pyqtSignal(list)

    def __init__(self, manager: ModManager):
        super().__init__()
        self._manager = manager

    def run(self):
        mods = self._manager.get_mods()
        self.loaded.emit(mods)


# ─────────────────────────────────────────────────────────────────────────────
# ModsPage
# ─────────────────────────────────────────────────────────────────────────────
class ModsPage(QWidget):
    favorite_changed = pyqtSignal(str, bool)
    request_new_game = pyqtSignal()
    mods_loaded = pyqtSignal()
    _MAJOR_GROUPS = ["Maps", "Placeables", "Transport", "Equipment", "Scripts"]
    _GROUP_CATEGORY_MAP = {
        "Maps": {"Map"},
        "Placeables": {"Placeable", "Shed", "Silo", "Factory", "Animal Pen"},
        "Transport": {"Truck", "Large Tractor", "Medium Tractor", "Small Tractor", "Front Loader", "Loader", "Weight"},
        "Equipment": {"Trailer", "Sprayer", "Mower", "Baler", "Seeder", "Plow", "Cultivator"},
        "Scripts": {"Script", "Mod"},
    }

    def __init__(self, manager: ModManager, favorites, parent=None, show_new_game_button: bool = False):
        super().__init__(parent)
        self._manager = manager
        self._favorites = favorites
        self._show_new_game_button = show_new_game_button
        self._new_game_emit_locked = False
        self._mods: list[ModInfo] = []
        self._selected_card = None
        self._filter_text = ""
        self._filter_state = "All mods"

        self._build_ui()
        self._load_mods()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        ttl = QLabel("⚙ Mod Manager")
        ttl.setObjectName("PageTitle")
        title_col.addWidget(ttl)
        sub = QLabel("Browse and remove mods")
        sub.setObjectName("PageSubtitle")
        title_col.addWidget(sub)

        hdr.addLayout(title_col, stretch=1)

        btn_refresh = QPushButton("Rescan for Mod")
        btn_refresh.setObjectName("ToolBtn")
        btn_refresh.setIcon(Icons.get_qicon(Icons.RESCAN))
        btn_refresh.setIconSize(QSize(18, 18))
        btn_refresh.setFixedSize(140, 36)
        btn_refresh.clicked.connect(self.reload_mods)
        hdr.addWidget(btn_refresh)

        if self._show_new_game_button:
            btn_new_game = QPushButton("New Game")
            btn_new_game.setObjectName("PrimaryBtn")
            btn_new_game.setIcon(Icons.get_qicon(Icons.PLUS))
            btn_new_game.setIconSize(QSize(18, 18))
            btn_new_game.setFixedSize(140, 36)
            btn_new_game.clicked.connect(self._emit_new_game_once)
            hdr.addWidget(btn_new_game)

        root.addLayout(hdr)

        # Stat row
        self._stat_row = QHBoxLayout()
        self._stat_row.setSpacing(16)
        self._stat_row.setContentsMargins(0, 8, 0, 8)
        self._stat_installed = StatCard("Installed", "…", "📦", "card_installed")
        self._stat_favorites = StatCard("Favourited", "…", "⭐", "card_favourited")
        self._stat_maps = StatCard("Maps", "…", "🗺️", "card_maps")
        self._stat_size = StatCard("Disk Usage", "…", "💾", "card_disk")
        for w in [self._stat_installed, self._stat_favorites, self._stat_maps, self._stat_size]:
            self._stat_row.addWidget(w)
        root.addLayout(self._stat_row)

        root.addWidget(HSeparator())

        # ── Filter toolbar ────────────────────────────────────────────────────
        from PyQt6.QtWidgets import QLineEdit
        flt = QHBoxLayout()
        flt.setSpacing(8)

        show_lbl = QLabel("SHOW:")
        show_lbl.setStyleSheet("color: #9ca3af; font-weight: bold; font-size: 13px;")
        flt.addWidget(show_lbl)
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All mods", "Favorites"] + self._MAJOR_GROUPS)
        self._filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #3b82f6;
            }
        """)
        self._filter_combo.currentTextChanged.connect(self._on_combo_filter)
        flt.addWidget(self._filter_combo)

        flt.addSpacing(32)

        self._search = QLineEdit()
        self._search.setObjectName("SearchBar")
        self._search.setPlaceholderText("Search…")
        self._search.setFixedWidth(200)
        self._search.textChanged.connect(self._on_search)
        flt.addWidget(self._search)

        flt.addStretch(1)

        root.addLayout(flt)
        root.addWidget(HSeparator())

        # ── Splitter: list | detail ───────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # Left: scroll list
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        self._fav_header = QLabel("⭐ Favourited Mods")
        self._fav_header.setObjectName("PageSubtitle")
        self._fav_header.setContentsMargins(8, 12, 8, 6)
        left_lay.addWidget(self._fav_header)

        self._favorite_grid = FavoriteModGrid()
        left_lay.addWidget(self._favorite_grid)

        self._fav_separator = HSeparator()
        left_lay.addWidget(self._fav_separator)

        self._fav_available_gap = QWidget()
        self._fav_available_gap.setFixedHeight(20)
        left_lay.addWidget(self._fav_available_gap)

        self._available_header = QLabel("Available Mods")
        self._available_header.setObjectName("PageSubtitle")
        self._available_header.setContentsMargins(8, 0, 8, 6)
        left_lay.addWidget(self._available_header)

        self._grid_view = ResponsiveModGrid()
        left_lay.addWidget(self._grid_view)

        splitter.addWidget(left)

        # Right: detail panel
        self._detail_panel = DetailPanel()
        self._detail_panel.delete_requested.connect(self._delete_mod)
        splitter.addWidget(self._detail_panel)

        splitter.setSizes([520, 320])
        root.addWidget(splitter, stretch=1)

    def _emit_new_game_once(self):
        """Prevent accidental duplicate New Game opens from repeated clicks/signals."""
        if self._new_game_emit_locked:
            return
        self._new_game_emit_locked = True
        self.request_new_game.emit()
        QTimer.singleShot(250, self._unlock_new_game_emit)

    def _unlock_new_game_emit(self):
        self._new_game_emit_locked = False

    def reload_mods(self) -> None:
        """Public API: trigger an asynchronous mods rescan."""
        self._load_mods()

    def get_loaded_mods(self) -> list[ModInfo]:
        """Public API: return a snapshot of currently loaded mods."""
        return list(self._mods)

    # ── Load ──────────────────────────────────────────────────────────────────
    def _load_mods(self):
        self._loader = ModLoaderThread(self._manager)
        self._loader.loaded.connect(self._on_mods_loaded)
        self._loader.start()

    def _on_mods_loaded(self, mods: list[ModInfo]):
        self._mods = mods
        self._populate_filter_options()
        self._refresh_cards()
        self.update_dashboard_stats()
        self.mods_loaded.emit()

    def _populate_filter_options(self):
        self._filter_combo.blockSignals(True)
        self._filter_combo.clear()

        options = ["All mods", "Favorites"] + self._MAJOR_GROUPS
        self._filter_combo.addItems(options)

        current = getattr(self, "_filter_state", "All mods")
        if current in options:
            self._filter_combo.setCurrentText(current)
        else:
            self._filter_combo.setCurrentText("All mods")
            self._filter_state = "All mods"

        self._filter_combo.blockSignals(False)

    def update_dashboard_stats(self):
        # Installed: count all loaded mods (including maps), independent of filters.
        self._stat_installed.set_value(str(len(self._mods)))
        
        # Favourited: count favorites across all loaded mods/maps.
        # Prefer stable mod IDs; fallback to filename for legacy favorites data.
        fav_count = sum(
            1
            for m in self._mods
            if self._favorites.is_favorite(m.id)
            or self._favorites.is_favorite(getattr(m, "filename", ""))
        )
        self._stat_favorites.set_value(str(fav_count))

        # Maps: count all map mods regardless of favorites/filter/view.
        map_count = sum(1 for m in self._mods if getattr(m, "category", "") == "Map")
        self._stat_maps.set_value(str(map_count))

        stats = self._manager.stats()
        size_gb = stats['size_mb'] / 1024.0
        self._stat_size.set_value(f"{size_gb:.1f} GB")

    # ── Cards ─────────────────────────────────────────────────────────────────
    def _refresh_cards(self):
        self._grid_view.clear_mods()
        self._favorite_grid.clear_mods()
        self._selected_card = None
        self._detail_panel.clear()

        visible = self._filtered_mods()
        for mod in visible:
            is_fav = self._favorites.is_favorite(mod.id)
            if is_fav:
                continue  # Skip favorited for the main grid

            thumbnail = ThumbnailLoader.obtain_local_pixmap(
                mod.icon_data,
                mod_id=mod.id,
                thumbnail_id=mod.thumbnail_id,
            )
                        
            card = self._grid_view.add_mod(
                mod.id,
                thumbnail,
                mod.title or mod.name,
                mod.version,
                False,
                mod.category,
                thumbnail_id=mod.thumbnail_id,
            )
            card.modClicked.connect(self._on_mod_clicked)
            card.favoriteToggled.connect(self._on_favorite_toggled)

        # Favorites grid (shows favorites regardless of filter)
        favorite_mods = [mod for mod in self._mods if self._favorites.is_favorite(mod.id)]
        for mod in favorite_mods:
            thumbnail = ThumbnailLoader.obtain_local_pixmap(
                mod.icon_data,
                mod_id=mod.id,
                thumbnail_id=mod.thumbnail_id,
            )
                        
            card = self._favorite_grid.add_mod(
                mod.id,
                thumbnail,
                mod.title or mod.name,
                mod.version,
                True,
                mod.category,
                thumbnail_id=mod.thumbnail_id,
            )
            card.modClicked.connect(self._on_mod_clicked)
            card.favoriteToggled.connect(self._on_favorite_toggled)

        has_favorites = len(favorite_mods) > 0
        self._fav_header.setVisible(has_favorites)
        self._favorite_grid.setVisible(has_favorites)
        self._fav_separator.setVisible(has_favorites)
        self._fav_available_gap.setVisible(has_favorites)

    def _on_mod_clicked(self, mod_id: str):
        for mod in self._filtered_mods():
            if mod.id == mod_id:
                self._select_card(None, mod)
                break

    def _filtered_mods(self) -> list[ModInfo]:
        result = self._mods
        state = getattr(self, "_filter_state", "All mods")

        if state == "Favorites":
            result = [m for m in result if self._favorites.is_favorite(m.id)]
        elif state in self._GROUP_CATEGORY_MAP:
            allowed_categories = self._GROUP_CATEGORY_MAP[state]
            result = [m for m in result if m.category in allowed_categories]

        if self._filter_text:
            q = self._filter_text.lower()
            result = [m for m in result
                      if q in (m.title or m.name).lower()
                      or q in (m.author or "").lower()]
        return result

    def _select_card(self, card, mod: ModInfo):
        if self._selected_card and hasattr(self._selected_card, "set_selected"):
            self._selected_card.set_selected(False)
        self._selected_card = card
        if card and hasattr(card, "set_selected"):
            card.set_selected(True)
        self._detail_panel.show_mod(mod)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _delete_mod(self, mod: ModInfo):
        reply = QMessageBox.question(
            self, "Delete Mod",
            f"Permanently delete '{mod.title or mod.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._manager.delete_mod(mod):
                self._favorites.set_favorite(mod.id, False)
                self._load_mods()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete mod.")

    def _on_favorite_toggled(self, mod_id: str, is_fav: bool):
        """Persist the new favourite state; move card between grids."""
        self._favorites.set_favorite(mod_id, is_fav)
        self.update_dashboard_stats()
        self._refresh_cards()
        self.favorite_changed.emit(mod_id, is_fav)

    def _on_search(self, text: str):
        self._filter_text = text
        self._refresh_cards()

    def _on_combo_filter(self, text: str):
        self._filter_state = text
        self._refresh_cards()


# ─────────────────────────────────────────────────────────────────────────────
# DetailPanel
# ─────────────────────────────────────────────────────────────────────────────
class DetailPanel(QWidget):
    delete_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        self._thumb_frame = QFrame()
        self._thumb_frame.setFixedSize(120, 120)
        self._thumb_frame.setStyleSheet(
            "background: #1e293b; border-radius: 12px;"
        )
        _thumb_inner = QVBoxLayout(self._thumb_frame)
        _thumb_inner.setContentsMargins(5, 5, 5, 5)
        _thumb_inner.setSpacing(0)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet(
            "background: transparent; border-radius: 8px; font-size: 48px;"
        )
        _thumb_inner.addWidget(self._icon_lbl)
        lay.addWidget(self._thumb_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("ModTitle")
        self._title_lbl.setFont(QFont("", 15, QFont.Weight.Bold))
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._title_lbl)
        
        self._current_mod: ModInfo | None = None

        self._meta_lbl = QLabel()
        self._meta_lbl.setObjectName("ModMeta")
        self._meta_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._meta_lbl.setWordWrap(True)
        lay.addWidget(self._meta_lbl)

        lay.addWidget(HSeparator())

        self._desc_lbl = QLabel()
        self._desc_lbl.setObjectName("ModAuthor")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(self._desc_lbl, stretch=1)

        self._delete_btn = QPushButton("DELETE")
        self._delete_btn.setObjectName("DetailDeleteBtn")
        self._delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_btn.setFixedSize(140, 36)
        self._delete_btn.setStyleSheet("""
            QPushButton#DetailDeleteBtn {
                background-color: transparent;
                color: #ef4444;
                border: 2px solid #ef4444;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.5px;
                padding: 2px 12px;
            }
            QPushButton#DetailDeleteBtn:hover {
                background-color: #ef4444;
                color: #ffffff;
                border: 2px solid #ef4444;
            }
            QPushButton#DetailDeleteBtn:pressed {
                background-color: #dc2626;
                color: #ffffff;
                border: 2px solid #dc2626;
            }
        """)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        self._delete_btn.hide()
        lay.addWidget(self._delete_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.clear()

    def clear(self):
        self._icon_lbl.setText("🌾")
        self._title_lbl.setText("Select a mod")
        self._meta_lbl.setText("")
        self._desc_lbl.setText("Click on a mod in the list\nto view details here.")
        self._current_mod = None
        self._delete_btn.hide()

    def show_mod(self, mod: ModInfo):
        self._current_mod = mod
        self._delete_btn.show()
        # icon
        pix = ThumbnailLoader.obtain_local_pixmap(
            mod.icon_data,
            mod_id=mod.id,
            thumbnail_id=mod.thumbnail_id,
        )
        if not pix.isNull():
            self._icon_lbl.setPixmap(
                pix.scaled(110, 110,
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self._icon_lbl.setText("🌾")
            self._icon_lbl.setPixmap(QPixmap())

        self._title_lbl.setText(mod.title or mod.name)

        meta_parts = []
        if mod.author:
            meta_parts.append(f"Author: {mod.author}")
        if mod.version:
            meta_parts.append(f"Version: {mod.version}")
        size_mb = round(mod.size_bytes / (1024 * 1024), 1)
        meta_parts.append(f"Size: {size_mb} MB")
        self._meta_lbl.setText("\n".join(meta_parts))

        self._desc_lbl.setText(
            mod.description or "No description available."
        )

    def _on_delete_clicked(self):
        if self._current_mod is None:
            QMessageBox.information(self, "Delete Mod", "Select a mod first.")
            return
        self.delete_requested.emit(self._current_mod)
