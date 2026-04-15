"""Tests for FavoritesManager persistence behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.favorites_manager import FavoritesManager


class TestFavoritesManager(unittest.TestCase):
    def test_load_from_dict_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "favorites.json"
            path.write_text(
                json.dumps({"favorites": ["modA", "modB", "modA", 1, ""]}),
                encoding="utf-8",
            )

            manager = FavoritesManager(str(path))

            self.assertEqual(manager.favorites, {"modA", "modB"})

    def test_load_from_legacy_list_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "favorites.json"
            path.write_text(json.dumps(["modA", "modC"]), encoding="utf-8")

            manager = FavoritesManager(str(path))

            self.assertEqual(manager.favorites, {"modA", "modC"})

    def test_malformed_payload_falls_back_to_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "favorites.json"
            path.write_text("{not-json", encoding="utf-8")

            manager = FavoritesManager(str(path))

            self.assertEqual(manager.favorites, set())

    def test_toggle_persists_sorted_favorites(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "favorites.json"
            manager = FavoritesManager(str(path))

            manager.toggle("modB")
            manager.toggle("modA")

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"favorites": ["modA", "modB"]})


if __name__ == "__main__":
    unittest.main()