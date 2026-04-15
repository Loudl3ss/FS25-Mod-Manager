"""Tests for RadioManager station and local music behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.radio_manager import RadioManager


class TestRadioManager(unittest.TestCase):
    def test_web_station_crud(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "streamingInternetRadios.xml"
            manager = RadioManager(str(xml_path))

            self.assertEqual(manager.get_web_stations(), [])
            self.assertTrue(manager.add_web_station(" https://example.com/radio "))
            self.assertFalse(manager.add_web_station("https://example.com/radio"))
            self.assertEqual(manager.get_web_stations(), ["https://example.com/radio"])
            self.assertTrue(manager.remove_web_station("https://example.com/radio"))
            self.assertFalse(manager.remove_web_station("https://example.com/radio"))

    def test_has_supported_music_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            music_dir = Path(tmpdir) / "music"
            music_dir.mkdir()
            (music_dir / "track1.mp3").write_text("x", encoding="utf-8")

            manager = RadioManager(str(Path(tmpdir) / "radio.xml"))
            self.assertTrue(manager.has_supported_music_files(str(music_dir)))

    def test_link_local_music_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source_music"
            source.mkdir()
            (source / "song.ogg").write_text("x", encoding="utf-8")

            target = Path(tmpdir) / "target" / "music"
            manager = RadioManager(str(Path(tmpdir) / "radio.xml"))

            ok, message = manager.link_local_music_folder(str(source), str(target))
            self.assertTrue(ok, message)
            self.assertTrue(target.is_symlink())
            self.assertEqual(manager.get_linked_music_folder(str(target)), str(source.resolve()))

    def test_get_linked_music_folder_for_plain_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "music"
            target.mkdir()
            manager = RadioManager(str(Path(tmpdir) / "radio.xml"))

            self.assertEqual(manager.get_linked_music_folder(str(target)), str(target))


if __name__ == "__main__":
    unittest.main()