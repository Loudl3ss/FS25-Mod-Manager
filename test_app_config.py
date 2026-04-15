"""Tests for AppConfigManager persistence and bootstrap behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.app_config import AppConfigManager


class TestAppConfigManager(unittest.TestCase):
    def test_bootstrap_migration_on_first_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            bootstrap = data_dir / "app_settings.json"
            bootstrap_payload = {
                "manager_cache_root": str(data_dir / "cache_root"),
                "mods_folder": "/mods",
                "savedgames_folder": "/saves",
            }
            bootstrap.write_text(json.dumps(bootstrap_payload), encoding="utf-8")

            manager = AppConfigManager(str(data_dir))

            self.assertEqual(manager.config.mods_folder, "/mods")
            self.assertEqual(manager.config.savedgames_folder, "/saves")
            self.assertTrue(Path(manager.config_path).exists())

    def test_save_syncs_main_and_bootstrap_configs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            manager = AppConfigManager(str(data_dir))
            manager.config.mods_folder = "/my/mods"
            manager.config.backup_folder = "/my/backups"

            manager.save()

            config_payload = json.loads(Path(manager.config_path).read_text(encoding="utf-8"))
            bootstrap_payload = json.loads(Path(manager.bootstrap_config_path).read_text(encoding="utf-8"))
            self.assertEqual(config_payload["mods_folder"], "/my/mods")
            self.assertEqual(config_payload["backup_folder"], "/my/backups")
            self.assertEqual(bootstrap_payload["mods_folder"], "/my/mods")
            self.assertEqual(bootstrap_payload["backup_folder"], "/my/backups")

    def test_read_json_invalid_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            manager = AppConfigManager(str(data_dir))
            bad_path = data_dir / "bad.json"
            bad_path.write_text("{bad-json", encoding="utf-8")

            self.assertEqual(manager._read_json(bad_path), {})


if __name__ == "__main__":
    unittest.main()