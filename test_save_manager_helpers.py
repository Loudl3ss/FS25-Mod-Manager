"""Focused tests for SaveManager internal helper behavior."""

from __future__ import annotations

import os
import tempfile
import unittest

from core.save_manager import SaveManager


class TestSaveManagerHelpers(unittest.TestCase):
    def test_safe_float_valid_and_invalid_values(self) -> None:
        self.assertEqual(SaveManager._safe_float("12.5"), 12.5)
        self.assertEqual(SaveManager._safe_float(10), 10.0)
        self.assertEqual(SaveManager._safe_float("bad", default=3.0), 3.0)
        self.assertEqual(SaveManager._safe_float(None, default=2.0), 2.0)

    def test_cleanup_partial_save_removes_existing_slot_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            slot = 4
            save_path = os.path.join(tmpdir, f"savegame{slot}")
            os.makedirs(save_path, exist_ok=True)

            manager._cleanup_partial_save(slot)

            self.assertFalse(os.path.exists(save_path))

    def test_cleanup_partial_save_ignores_missing_and_none_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            manager._cleanup_partial_save(None)
            manager._cleanup_partial_save(999)


if __name__ == "__main__":
    unittest.main()

class TestDeleteSave(unittest.TestCase):
    def _manager(self, tmp: str):
        return SaveManager(tmp, backup_dir=os.path.join(tmp, "bk"),
                           default_backup_base=os.path.join(tmp, "bk"))

    def test_delete_save_removes_the_slot_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            slot_dir = os.path.join(tmp, "savegame1")
            os.makedirs(os.path.join(slot_dir, "nested"))
            with open(os.path.join(slot_dir, "careerSavegame.xml"), "w") as fh:
                fh.write("<careerSavegame/>")

            manager = self._manager(tmp)
            self.assertTrue(manager.get_save(1).exists)

            ok, _ = manager.delete_save(1)
            self.assertTrue(ok)
            self.assertFalse(os.path.exists(slot_dir))
            # A deleted slot must not report itself as still present.
            self.assertFalse(manager.get_save(1).exists)

    def test_delete_save_reports_missing_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, message = self._manager(tmp).delete_save(4)
            self.assertFalse(ok)
            self.assertIn("does not exist", message)
