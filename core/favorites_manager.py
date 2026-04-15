"""Persistent storage of favourite mod IDs."""
from __future__ import annotations

import json
from pathlib import Path


class FavoritesManager:
    """Persists a set of favourite mod IDs to a JSON file."""

    def __init__(self, config_path: str):
        self._path = Path(config_path)
        self._favorites: set[str] = set()
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    @staticmethod
    def _parse_favorites_payload(payload: object) -> set[str]:
        """Parse favorites payload from supported JSON shapes."""
        if isinstance(payload, dict):
            raw = payload.get("favorites", [])
        elif isinstance(payload, list):
            raw = payload
        else:
            raw = []

        if not isinstance(raw, list):
            return set()

        return {item for item in raw if isinstance(item, str) and item.strip()}

    def _load(self):
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._favorites = self._parse_favorites_payload(data)
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
    def is_favorite(self, mod_id: str) -> bool:
        return mod_id in self._favorites

    def set_favorite(self, mod_id: str, is_fav: bool):
        """Explicitly set the favourite state and persist."""
        if is_fav:
            self._favorites.add(mod_id)
        else:
            self._favorites.discard(mod_id)
        self._save()

    def toggle(self, mod_id: str) -> bool:
        """Toggle and persist. Returns new state (True = now favourite)."""
        is_fav = mod_id not in self._favorites
        self.set_favorite(mod_id, is_fav)
        return is_fav

    @property
    def count(self) -> int:
        return len(self._favorites)

    @property
    def favorites(self) -> set[str]:
        return set(self._favorites)
