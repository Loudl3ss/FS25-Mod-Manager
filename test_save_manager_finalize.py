"""Focused tests for SaveManager.finalize_new_game edge behavior."""

from __future__ import annotations

import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from types import SimpleNamespace

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

    def test_finalize_resolves_map_from_mod_manager_and_marks_required_mod(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)

            map_mod = SimpleNamespace(
                id="map_mod_id",
                filename="FS25_MyMap.zip",
                name="FS25_MyMap",
                title="My Test Map",
                version="1.2.3.4",
            )
            tool_mod = SimpleNamespace(
                id="tool_mod_id",
                filename="FS25_Tools.zip",
                name="FS25_Tools",
                title="Tool Pack",
                version="2.0.0.0",
            )

            fake_mod_manager = SimpleNamespace(get_mods=lambda: [map_mod, tool_mod])

            session = NewGameSession(
                selected_map="map_mod_id",
                selected_mods=["tool_mod_id"],
            )
            success, _ = manager.finalize_new_game(session, fake_mod_manager)

            career_xml = os.path.join(tmpdir, "savegame1", "careerSavegame.xml")
            self.assertTrue(success)
            self.assertTrue(os.path.exists(career_xml))

            tree = ET.parse(career_xml)
            root = tree.getroot()

            self.assertEqual(root.findtext("settings/mapId"), "FS25_MyMap")
            self.assertEqual(root.findtext("settings/mapTitle"), "My Test Map")

            mod_nodes = root.findall("mod")
            by_name = {node.get("modName"): node for node in mod_nodes}
            self.assertIn("FS25_MyMap", by_name)
            self.assertIn("FS25_Tools", by_name)
            self.assertEqual(by_name["FS25_MyMap"].get("required"), "true")
            self.assertEqual(by_name["FS25_Tools"].get("required"), "false")

    def test_finalize_deduplicates_map_mod_when_selected_mods_repeat_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SaveManager(tmpdir)

            map_mod = SimpleNamespace(
                id="map_mod_id",
                filename="FS25_MyMap.zip",
                name="FS25_MyMap",
                title="My Test Map",
                version="1.2.3.4",
            )

            fake_mod_manager = SimpleNamespace(get_mods=lambda: [map_mod])

            session = NewGameSession(
                selected_map="map_mod_id",
                selected_mods=["map_mod_id", "map_mod_id"],
            )
            success, _ = manager.finalize_new_game(session, fake_mod_manager)

            career_xml = os.path.join(tmpdir, "savegame1", "careerSavegame.xml")
            self.assertTrue(success)

            tree = ET.parse(career_xml)
            root = tree.getroot()
            mod_names = [node.get("modName") for node in root.findall("mod")]

            self.assertEqual(mod_names.count("FS25_MyMap"), 1)


if __name__ == "__main__":
    unittest.main()
