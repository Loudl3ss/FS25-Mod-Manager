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