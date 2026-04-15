"""Tests for SettingsManager parsing and load behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.settings_manager import SettingsManager


class TestSettingsManager(unittest.TestCase):
    def test_parse_helpers_with_invalid_values(self) -> None:
        self.assertEqual(SettingsManager._parse_int("5", 1), 5)
        self.assertEqual(SettingsManager._parse_int("bad", 2), 2)

        self.assertEqual(SettingsManager._parse_float("2.5", 1.0), 2.5)
        self.assertEqual(SettingsManager._parse_float("bad", 1.5), 1.5)

        self.assertTrue(SettingsManager._parse_bool("true", False))
        self.assertTrue(SettingsManager._parse_bool("1", False))
        self.assertFalse(SettingsManager._parse_bool("no", True))
        self.assertTrue(SettingsManager._parse_bool(None, True))

    def test_load_uses_defaults_for_invalid_numeric_values(self) -> None:
        xml = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<gameSettings>
    <difficulty>abc</difficulty>
    <economyDifficulty>3</economyDifficulty>
    <loanAnnualInterestRate>invalid</loanAnnualInterestRate>
    <priceChangeRange>0.4</priceChangeRange>
    <fuelUsage>x</fuelUsage>
    <dirtInterval>2</dirtInterval>
    <vehicleDamageAge>1</vehicleDamageAge>
    <plowingRequiredEnabled>yes</plowingRequiredEnabled>
    <stoneEnabled>no</stoneEnabled>
    <weedsEnabled>1</weedsEnabled>
    <limeRequired>0</limeRequired>
    <isSnowEnabled>true</isSnowEnabled>
</gameSettings>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "gameSettings.xml"
            path.write_text(xml, encoding="utf-8")

            mgr = SettingsManager(str(path))
            settings = mgr.load()

            self.assertEqual(settings.difficulty, 2)
            self.assertEqual(settings.economy_difficulty, 3)
            self.assertEqual(settings.loan_interest_rate, 6.0)
            self.assertEqual(settings.price_change_range, 0.4)
            self.assertEqual(settings.fuel_usage, 2)
            self.assertEqual(settings.dirt_interval, 2)
            self.assertEqual(settings.vehicle_damage_age, 1)
            self.assertTrue(settings.plowing_required)
            self.assertFalse(settings.stones_enabled)
            self.assertTrue(settings.weeds_enabled)
            self.assertFalse(settings.lime_required)
            self.assertTrue(settings.snow_enabled)


if __name__ == "__main__":
    unittest.main()