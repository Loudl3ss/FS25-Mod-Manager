"""Tests for ModManager thumbnail cache behavior."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.mod_manager import ModInfo, ModManager


class TestModManagerThumbnailCache(unittest.TestCase):
    def test_save_and_load_thumbnail_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            manager = ModManager(str(mods_dir))

            mod = ModInfo(
                name="Example Mod",
                filename="example.zip",
                filepath=str(mods_dir / "example.zip"),
                is_enabled=True,
                is_zip=True,
                id="mod123",
            )
            icon_bytes = b"fake-thumb-data"

            thumbnail_id = manager.save_thumbnail(mod, icon_bytes)
            loaded_data, loaded_id = manager.load_thumbnail(mod.id)

            self.assertEqual(thumbnail_id, loaded_id)
            self.assertEqual(icon_bytes, loaded_data)
            self.assertEqual(mod.thumbnail_id, thumbnail_id)

    def test_load_thumbnail_drops_stale_db_record_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            manager = ModManager(str(mods_dir))

            mod = ModInfo(
                name="Example Mod",
                filename="example.zip",
                filepath=str(mods_dir / "example.zip"),
                is_enabled=True,
                is_zip=True,
                id="mod456",
            )
            icon_bytes = b"thumb-data"
            manager.save_thumbnail(mod, icon_bytes)

            record = manager._get_thumbnail_record(mod.id)
            self.assertIsNotNone(record)
            thumb_file = Path(manager.thumbnails_path) / record["cache_filename"]
            thumb_file.unlink()

            loaded_data, loaded_id = manager.load_thumbnail(mod.id)
            self.assertIsNone(loaded_data)
            self.assertEqual("", loaded_id)
            self.assertIsNone(manager._get_thumbnail_record(mod.id))

    def test_cleanup_thumbnails_removes_unreferenced_entries_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            manager = ModManager(str(mods_dir))

            active_mod = ModInfo(
                name="Active Mod",
                filename="active.zip",
                filepath=str(mods_dir / "active.zip"),
                is_enabled=True,
                is_zip=True,
                id="active1",
            )
            stale_mod = ModInfo(
                name="Stale Mod",
                filename="stale.zip",
                filepath=str(mods_dir / "stale.zip"),
                is_enabled=True,
                is_zip=True,
                id="stale1",
            )

            active_thumb = manager.save_thumbnail(active_mod, b"active-thumb")
            stale_thumb = manager.save_thumbnail(stale_mod, b"stale-thumb")

            manager.cleanup_thumbnails({active_mod.id})

            self.assertIsNotNone(manager._get_thumbnail_record(active_mod.id))
            self.assertIsNone(manager._get_thumbnail_record(stale_mod.id))
            self.assertTrue(Path(manager.get_thumbnail_path(active_thumb)).exists())
            self.assertFalse(Path(manager.get_thumbnail_path(stale_thumb)).exists())

    def test_get_thumbnail_record_returns_none_on_database_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            mods_dir = Path(tmpdir) / "mods"
            manager = ModManager(str(mods_dir))

            with sqlite3.connect(manager.thumbnail_db_path) as conn:
                conn.execute("DROP TABLE thumbnail_cache")
                conn.commit()

            self.assertIsNone(manager._get_thumbnail_record("any-id"))


if __name__ == "__main__":
    unittest.main()
