"""Focused tests for SaveManager.finalize_new_game edge behavior."""

from __future__ import annotations

import os
import tempfile
import unittest

from core.new_game_session import NewGameSession
from core.save_manager import SaveManager


class TestSaveManagerFinalize(unittest.TestCase):
    def test_finalize_fails_when_no_map_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            session = NewGameSession()

            success, message = manager.finalize_new_game(session)

        self.assertFalse(success)
        self.assertEqual(message, "No map selected")

    def test_finalize_fails_when_all_slots_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            for slot in range(1, manager.MAX_SLOTS + 1):
                save_path = os.path.join(tmpdir, f"savegame{slot}")
                os.makedirs(save_path, exist_ok=True)
                with open(os.path.join(save_path, "careerSavegame.xml"), "w", encoding="utf-8") as handle:
                    handle.write("<careerSavegame />")

            session = NewGameSession(selected_map="my_map")
            success, message = manager.finalize_new_game(session)

        self.assertFalse(success)
        self.assertEqual(message, "All save slots are full")

    def test_finalize_prefers_reusable_existing_slot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            os.makedirs(os.path.join(tmpdir, "savegame1"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "savegame2"), exist_ok=True)
            with open(os.path.join(tmpdir, "savegame2", "careerSavegame.xml"), "w", encoding="utf-8") as handle:
                handle.write("<careerSavegame />")

            session = NewGameSession(selected_map="my_map")
            success, message = manager.finalize_new_game(session)

            slot1_career = os.path.join(tmpdir, "savegame1", "careerSavegame.xml")
            slot3_dir = os.path.join(tmpdir, "savegame3")

            self.assertTrue(success)
            self.assertIn("save slot 1", message)
            self.assertTrue(os.path.exists(slot1_career))
            self.assertFalse(os.path.exists(slot3_dir))

    def test_finalize_cleans_partial_folder_on_generation_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)
            session = NewGameSession(selected_map="my_map")

            original = manager._generate_career_savegame_xml

            def raise_write_error(*args, **kwargs):
                raise OSError("disk full")

            manager._generate_career_savegame_xml = raise_write_error  # type: ignore[method-assign]
            try:
                success, message = manager.finalize_new_game(session)
            finally:
                manager._generate_career_savegame_xml = original  # type: ignore[method-assign]

            slot1_dir = os.path.join(tmpdir, "savegame1")

        self.assertFalse(success)
        self.assertIn("Failed to create game", message)
        self.assertFalse(os.path.exists(slot1_dir))


if __name__ == "__main__":
    unittest.main()
