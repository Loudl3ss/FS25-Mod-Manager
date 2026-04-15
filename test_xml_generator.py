"""Unit tests for CareerXmlBuilder output and conversions."""

from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from core.xml_generator import CareerXmlBuilder


class TestCareerXmlBuilder(unittest.TestCase):
    def test_build_tree_maps_timescale_and_difficulty(self) -> None:
        builder = CareerXmlBuilder(
            settings={
                "farmName": "My Farm",
                "mapId": "my_map",
                "mapTitle": "My Map",
                "timeScale": "30x",
                "economicDifficulty": 3,
                "money": "750000",
            }
        )

        root = builder.build_tree().getroot()
        settings = root.find("settings")

        self.assertIsNotNone(settings)
        self.assertEqual(settings.findtext("timeScale"), "30.000000")
        self.assertEqual(settings.findtext("economicDifficulty"), "HARD")
        self.assertEqual(settings.findtext("initialMoney"), "750000")

    def test_build_tree_marks_selected_map_mod_as_required(self) -> None:
        builder = CareerXmlBuilder(
            settings={"mapId": "my_map"},
            mods=[
                {"id": "my_map", "modName": "FS25_MyMap", "title": "My Map", "version": "1.0.0.0"},
                {"id": "tractor_pack", "modName": "FS25_TractorPack", "title": "Tractor Pack", "version": "1.0.0.0"},
            ],
        )

        root = builder.build_tree().getroot()
        mods = root.findall("mod")

        self.assertEqual(len(mods), 2)
        required_by_name = {m.get("modName"): m.get("required") for m in mods}
        self.assertEqual(required_by_name.get("FS25_MyMap"), "true")
        self.assertEqual(required_by_name.get("FS25_TractorPack"), "false")

    def test_to_int_and_to_float_use_defaults_for_bad_values(self) -> None:
        self.assertEqual(CareerXmlBuilder._to_int("7", default=0), 7)
        self.assertEqual(CareerXmlBuilder._to_int("bad", default=5), 5)
        self.assertEqual(CareerXmlBuilder._to_float("2.5", default=0.0), 2.5)
        self.assertEqual(CareerXmlBuilder._to_float(None, default=1.25), 1.25)

    def test_write_persists_valid_xml_file(self) -> None:
        builder = CareerXmlBuilder(settings={"farmName": "Write Test", "mapId": "write_map"})

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "careerSavegame.xml"
            builder.write(str(output))

            self.assertTrue(output.exists())
            tree = ET.parse(output)
            root = tree.getroot()
            self.assertEqual(root.tag, "careerSavegame")
            self.assertEqual(root.findtext("settings/mapId"), "write_map")


if __name__ == "__main__":
    unittest.main()
