"""Mods management page."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
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

    def __init__(self, manager: ModManager, favorites, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._favorites = favorites
        self._mods: list[ModInfo] = []
        self._selected_card = None
        self._filter_text = ""
        self._filter_state = "all"   # all / enabled / disabled / favorites

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
        sub = QLabel("Enable, disable or remove mods")
        sub.setObjectName("PageSubtitle")
        title_col.addWidget(sub)

        hdr.addLayout(title_col, stretch=1)

        btn_open = QPushButton("📂 Open Folder")
        btn_open.setObjectName("ToolBtn")
        btn_open.clicked.connect(self._open_folder)
        hdr.addWidget(btn_open)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setObjectName("ToolBtn")
        btn_refresh.clicked.connect(self._load_mods)
        hdr.addWidget(btn_refresh)

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

        self._search = QLineEdit()
        self._search.setObjectName("SearchBar")
        self._search.setPlaceholderText("🔍  Search mods…")
        self._search.textChanged.connect(self._on_search)
        flt.addWidget(self._search, stretch=1)

        show_lbl = QLabel("SHOW:")
        show_lbl.setStyleSheet("color: #9ca3af; font-weight: bold; font-size: 13px;")
        flt.addWidget(show_lbl)
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All mods", "Favorites", "Maps", "Vehicles", "Scripts"])
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

        fav_header = QLabel("⭐ Favourited Mods")
        fav_header.setObjectName("PageSubtitle")
        fav_header.setContentsMargins(8, 12, 8, 6)
        left_lay.addWidget(fav_header)

        self._favorite_grid = ResponsiveModGrid()
        self._favorite_grid.setFixedHeight(210)
        left_lay.addWidget(self._favorite_grid)

        left_lay.addWidget(HSeparator())

        self._grid_view = ResponsiveModGrid()
        left_lay.addWidget(self._grid_view)

        splitter.addWidget(left)

        # Right: detail panel
        self._detail_panel = DetailPanel()
        splitter.addWidget(self._detail_panel)

        splitter.setSizes([520, 320])
        root.addWidget(splitter, stretch=1)

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

    def _populate_filter_options(self):
        categories = {m.category for m in self._mods if m.category}
        sorted_cats = sorted(list(categories))
        
        self._filter_combo.blockSignals(True)
        self._filter_combo.clear()
        
        options = ["All mods", "Favorites"] + sorted_cats
        self._filter_combo.addItems(options)
        
        current = getattr(self, "_filter_state", "All mods")
        if current in options:
            self._filter_combo.setCurrentText(current)
        else:
            self._filter_combo.setCurrentText("All mods")
            self._filter_state = "All mods"
            
        self._filter_combo.blockSignals(False)

    def update_dashboard_stats(self):
        stats = self._manager.stats()
        self._stat_installed.set_value(str(stats["total"]))
        
        fav_count = sum(1 for m in self._mods if self._favorites.is_favorite(m.filename))
        self._stat_favorites.set_value(str(fav_count))
        
        map_count = sum(1 for card in self._grid_view._cards if hasattr(card, "category") and card.category == "Map")
        self._stat_maps.set_value(str(map_count))
        
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
            is_fav = self._favorites.is_favorite(mod.filename)
            if is_fav:
                continue  # Skip favorited for the main grid
            
            thumbnail = QPixmap()
            if mod.icon_data:
                if not thumbnail.loadFromData(mod.icon_data) or thumbnail.isNull():
                    try:
                        from io import BytesIO
                        from PIL import Image
                        from PyQt6.QtGui import QImage
                        img = Image.open(BytesIO(mod.icon_data)).convert("RGBA")
                        qim = QImage(img.tobytes("raw", "RGBA"), img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                        thumbnail = QPixmap.fromImage(qim)
                    except Exception:
                        pass
                        
            card = self._grid_view.add_mod(mod.filename, thumbnail, mod.title or mod.name, mod.version, False, mod.category)
            card.modClicked.connect(self._on_mod_clicked)
            card.favoriteToggled.connect(self._on_favorite_toggled)

        # Favorites grid (shows favorites regardless of filter)
        favorite_mods = [mod for mod in self._mods if self._favorites.is_favorite(mod.filename)]
        for mod in favorite_mods:
            thumbnail = QPixmap()
            if mod.icon_data:
                if not thumbnail.loadFromData(mod.icon_data) or thumbnail.isNull():
                    try:
                        from io import BytesIO
                        from PIL import Image
                        from PyQt6.QtGui import QImage
                        img = Image.open(BytesIO(mod.icon_data)).convert("RGBA")
                        qim = QImage(img.tobytes("raw", "RGBA"), img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                        thumbnail = QPixmap.fromImage(qim)
                    except Exception:
                        pass
                        
            card = self._favorite_grid.add_mod(mod.filename, thumbnail, mod.title or mod.name, mod.version, True, mod.category)
            card.modClicked.connect(self._on_mod_clicked)
            card.favoriteToggled.connect(self._on_favorite_toggled)

    def _on_mod_clicked(self, mod_id: str):
        for mod in self._filtered_mods():
            if mod.filename == mod_id:
                self._select_card(None, mod)
                break

    def _filtered_mods(self) -> list[ModInfo]:
        result = self._mods
        state = getattr(self, "_filter_state", "All mods")
        
        if state == "Favorites":
            result = [m for m in result if self._favorites.is_favorite(m.filename)]
        elif state != "All mods":
            result = [m for m in result if m.category == state]

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
                self._load_mods()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete mod.")

    def _on_favorite_toggled(self, mod_id: str, is_fav: bool):
        """Persist the new favourite state; move card between grids."""
        self._favorites.set_favorite(mod_id, is_fav)
        self.update_dashboard_stats()
        self._refresh_cards()
        self.favorite_changed.emit(mod_id, is_fav)

    def _open_folder(self):
        self._manager.open_folder()

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setFixedHeight(120)
        self._icon_lbl.setStyleSheet(
            "border-radius: 12px; background: #1e293b; font-size: 48px;"
        )
        lay.addWidget(self._icon_lbl)

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

        self.clear()

    def clear(self):
        self._icon_lbl.setText("🌾")
        self._title_lbl.setText("Select a mod")
        self._meta_lbl.setText("")
        self._desc_lbl.setText("Click on a mod in the list\nto view details here.")
        self._current_mod = None

    def show_mod(self, mod: ModInfo):
        self._current_mod = mod
        # icon
        if mod.icon_data:
            pix = QPixmap()
            if pix.loadFromData(mod.icon_data) and not pix.isNull():
                self._icon_lbl.setPixmap(
                    pix.scaled(120, 120,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                )
            else:
                try:
                    from io import BytesIO
                    from PIL import Image
                    from PyQt6.QtGui import QImage
                    img = Image.open(BytesIO(mod.icon_data)).convert("RGBA")
                    qim = QImage(img.tobytes("raw", "RGBA"), img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                    pix = QPixmap.fromImage(qim)
                    self._icon_lbl.setPixmap(
                        pix.scaled(120, 120,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                    )
                except Exception:
                    self._icon_lbl.setText("🌾")
                    self._icon_lbl.setPixmap(QPixmap())
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
