"""Persistent storage of favourite mod filenames."""
from __future__ import annotations

import json
from pathlib import Path


class FavoritesManager:
    """Persists a set of favourite mod filenames to a JSON file."""

    def __init__(self, config_path: str):
        self._path = Path(config_path)
        self._favorites: set[str] = set()
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._favorites = set(data.get("favorites", []))
        except Exception as e:
            print(f"Favorites load error: {e}")
            self._favorites = set()

    def _save(self):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"favorites": sorted(self._favorites)}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"Favorites save error: {e}")

    # ── API ───────────────────────────────────────────────────────────────────
    def is_favorite(self, filename: str) -> bool:
        return filename in self._favorites

    def set_favorite(self, filename: str, is_fav: bool):
        """Explicitly set the favourite state and persist."""
        if is_fav:
            self._favorites.add(filename)
        else:
            self._favorites.discard(filename)
        self._save()

    def toggle(self, filename: str) -> bool:
        """Toggle and persist. Returns new state (True = now favourite)."""
        is_fav = filename not in self._favorites
        self.set_favorite(filename, is_fav)
        return is_fav

    @property
    def count(self) -> int:
        return len(self._favorites)

    @property
    def favorites(self) -> set[str]:
        return set(self._favorites)
