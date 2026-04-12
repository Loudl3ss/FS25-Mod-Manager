"""Dedicated subclasses for Library pages."""
from __future__ import annotations

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QPushButton

from core.thumbnail_loader import ThumbnailLoader
from ui.mods_page import ModsPage


class _LibraryBasePage(ModsPage):
    """Shared behavior for read-focused library views."""

    TARGET_FILTER = "All mods"

    def __init__(self, manager, favorites, app_config_manager=None, parent=None):
        self._app_config_manager = app_config_manager
        super().__init__(manager, favorites, parent=parent)
        self._apply_library_mode()

    def _apply_library_mode(self):
        # Lock the filter to the target view to keep each page focused.
        if hasattr(self, "_filter_combo"):
            self._filter_combo.setCurrentText(self.TARGET_FILTER)
            self._filter_combo.setEnabled(False)

        # Hide edit-oriented buttons in library-only views.
        for btn in self.findChildren(QPushButton):
            if btn.text() in {"📂 Open Folder", "🔄 Refresh"}:
                btn.hide()

    def _is_map_mod(self, mod) -> bool:
        return "map" in (mod.category or "").lower()

    def _build_thumbnail(self, mod) -> QPixmap:
        return ThumbnailLoader.obtain_local_pixmap(
            mod.icon_data,
            mod_id=mod.id,
            thumbnail_id=mod.thumbnail_id,
        )

    def _apply_search(self, mods):
        if not self._filter_text:
            return mods
        q = self._filter_text.lower()
        return [
            m
            for m in mods
            if q in (m.title or m.name).lower() or q in (m.author or "").lower()
        ]

    def _hide_favorites_strip(self):
        self._favorite_grid.hide()
        parent = self._favorite_grid.parentWidget()
        lay = parent.layout() if parent is not None else None
        if lay is None:
            return

        for i in range(lay.count()):
            item = lay.itemAt(i)
            w = item.widget() if item is not None else None
            if w is self._favorite_grid:
                if i - 1 >= 0:
                    prev_item = lay.itemAt(i - 1)
                    prev = prev_item.widget() if prev_item is not None else None
                    if isinstance(prev, QLabel):
                        prev.hide()
                if i + 1 < lay.count():
                    next_item = lay.itemAt(i + 1)
                    nxt = next_item.widget() if next_item is not None else None
                    if nxt is not None:
                        nxt.hide()
                break

    def _render_single_grid(self, visible):
        # One-grid read-only mode for library pages.
        self._grid_view.clear_mods()
        self._favorite_grid.clear_mods()
        self._selected_card = None
        self._detail_panel.clear()

        for mod in visible:
            card = self._grid_view.add_mod(
                mod.id,
                self._build_thumbnail(mod),
                mod.title or mod.name,
                mod.version,
                self._favorites.is_favorite(mod.id),
                mod.category,
                thumbnail_id=mod.thumbnail_id,
            )
            card.modClicked.connect(self._on_mod_clicked)
            if hasattr(card, "fav_btn"):
                card.fav_btn.hide()

        self._hide_favorites_strip()
        self._grid_view.show()

    def _on_favorite_toggled(self, mod_id: str, is_fav: bool):
        # Library pages are read-only and should not mutate favorite state.
        return


class LibraryFavoritesPage(_LibraryBasePage):
    """Dedicated page for Favorite mods."""
    TARGET_FILTER = "Favorites"

    def _refresh_cards(self):
        visible = [mod for mod in self._mods if self._favorites.is_favorite(mod.id)]
        self._render_single_grid(self._apply_search(visible))


class LibraryModsPage(_LibraryBasePage):
    """Dedicated page for All Mods (Library view)."""
    TARGET_FILTER = "All mods"

    def _refresh_cards(self):
        cfg = getattr(self._app_config_manager, "config", None)

        show_favorites = getattr(cfg, "show_favorites_in_all_mods", False) if cfg else False
        include_maps = getattr(cfg, "include_maps_in_all_mods", False) if cfg else False
        strict_maps = getattr(cfg, "strict_map_filtering", True) if cfg else True

        visible = list(self._mods)

        # Strict map filtering always removes maps from All Mods.
        if strict_maps or not include_maps:
            visible = [m for m in visible if not self._is_map_mod(m)]

        # Optionally remove favorited items from All Mods.
        if not show_favorites:
            visible = [m for m in visible if not self._favorites.is_favorite(m.id)]

        self._render_single_grid(self._apply_search(visible))


class LibraryMapsPage(_LibraryBasePage):
    """Dedicated page for Map mods."""
    TARGET_FILTER = "Maps"

    def _refresh_cards(self):
        visible = [mod for mod in self._mods if self._is_map_mod(mod)]
        self._render_single_grid(self._apply_search(visible))
