"""Builder for FS25 careerSavegame.xml files."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Optional


# Default values matching FS25 defaults.
DEFAULTS: dict[str, object] = {
    # General
    "farmName": "My Farm",
    "savegameName": "New Save",
    "mapId": "",
    "mapTitle": "",
    "economicDifficulty": 2,        # 1=Easy, 2=Normal, 3=Hard
    "timeScale": "5x",
    "autoSaveInterval": 0,          # 0=Off, 5, 10, 15
    "money": 500000,
    "loan": 0,
    "trafficEnabled": True,
    "snowEnabled": True,
    "ownFarm": False,
    "guidedTour": False,
    # Seasons
    "seasonalGrowth": 1,            # 1=Yes, 2=No, 3=Paused
    "daysPerMonth": 1,
    "fixedVisualMonth": False,
    # Crops and Growth
    "cropDestruction": True,
    "plowingRequired": True,
    "fieldstoneEnabled": True,
    "limeRequired": True,
    "weedsEnabled": True,
    "disasterDestruction": 2,       # 0=Disabled, 1=Visuals, 2=Enabled
    # Vehicle Controls
    "dirtInterval": 1,              # 1=Normal, 2=Fast, 3=Slow, 4=Off
    "autoEngineStart": True,
    "stopAndGoBraking": True,
    "trailerFillLimit": False,
    "fuelUsage": 2,                 # 1=Low, 2=Normal, 3=High
    # AI Workers
    "aiRefillFuel": 0,
    "aiRefillSeeds": 0,
    "aiRefillFertilizer": 0,
    "aiRefillSlurry": 0,
    "aiRefillManure": 0,
}

# Map timescale UI strings to numeric values.
TIMESCALE_MAP = {
    "Real Time": 1,
    "5x": 5,
    "15x": 15,
    "30x": 30,
    "60x": 60,
    "120x": 120,
}


class CareerXmlBuilder:
    """Builds a complete careerSavegame.xml from a settings dictionary."""

    def __init__(self, settings: Optional[dict] = None, mods: Optional[list] = None):
        self._settings = dict(DEFAULTS)
        if settings:
            self._settings.update(settings)
        self._mods = mods or []

    def _val(self, key: str):
        """Get a setting value with fallback to default."""
        return self._settings.get(key, DEFAULTS.get(key))

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        """Convert a dynamic value to int with safe fallback."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """Convert a dynamic value to float with safe fallback."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _bool_str(self, key: str) -> str:
        """Convert a setting to XML boolean string."""
        val = self._val(key)
        return "true" if val else "false"

    def _int_str(self, key: str) -> str:
        """Convert a setting to integer string."""
        return str(self._to_int(self._val(key), 0))

    def build_tree(self) -> ET.ElementTree:
        """Build the full XML tree matching real FS25 layout."""
        root = ET.Element("careerSavegame")
        root.set("revision", "2")
        root.set("valid", "true")

        # <settings>
        settings = ET.SubElement(root, "settings")

        ET.SubElement(settings, "savegameName").text = str(self._val("farmName") or "New Save")
        ET.SubElement(settings, "creationDate").text = datetime.now().strftime("%Y-%m-%d")
        ET.SubElement(settings, "mapId").text = str(self._val("mapId") or "")
        ET.SubElement(settings, "mapTitle").text = str(self._val("mapTitle") or self._val("mapId") or "")

        now_date = datetime.now().strftime("%Y-%m-%d")
        ET.SubElement(settings, "saveDateFormatted").text = now_date
        ET.SubElement(settings, "saveDate").text = now_date

        ET.SubElement(settings, "initialMoney").text = str(self._to_int(self._val("money"), 0))
        ET.SubElement(settings, "initialLoan").text = str(self._to_int(self._val("loan"), 0))

        # Difficulty mapping
        diff_val = self._val("economicDifficulty")
        diff_map = {1: "EASY", 2: "NORMAL", 3: "HARD"}
        ET.SubElement(settings, "economicDifficulty").text = diff_map.get(self._to_int(diff_val, 2), "NORMAL")

        ET.SubElement(settings, "hasInitiallyOwnedFarmlands").text = self._bool_str("ownFarm")
        ET.SubElement(settings, "loadDefaultFarm").text = self._bool_str("ownFarm")
        ET.SubElement(settings, "startWithGuidedTour").text = self._bool_str("guidedTour")
        ET.SubElement(settings, "trafficEnabled").text = self._bool_str("trafficEnabled")
        ET.SubElement(settings, "stopAndGoBraking").text = self._bool_str("stopAndGoBraking")
        ET.SubElement(settings, "trailerFillLimit").text = self._bool_str("trailerFillLimit")
        ET.SubElement(settings, "automaticMotorStartEnabled").text = self._bool_str("autoEngineStart")
        ET.SubElement(settings, "growthMode").text = self._int_str("seasonalGrowth")
        ET.SubElement(settings, "plannedDaysPerPeriod").text = self._int_str("daysPerMonth")
        ET.SubElement(settings, "fruitDestruction").text = self._bool_str("cropDestruction")
        ET.SubElement(settings, "plowingRequiredEnabled").text = self._bool_str("plowingRequired")
        ET.SubElement(settings, "stonesEnabled").text = self._bool_str("fieldstoneEnabled")
        ET.SubElement(settings, "weedsEnabled").text = self._bool_str("weedsEnabled")
        ET.SubElement(settings, "limeRequired").text = self._bool_str("limeRequired")
        ET.SubElement(settings, "isSnowEnabled").text = self._bool_str("snowEnabled")
        ET.SubElement(settings, "fuelUsage").text = self._int_str("fuelUsage")

        # AI helpers
        ET.SubElement(settings, "helperBuyFuel").text = "true" if self._to_int(self._val("aiRefillFuel"), 0) == 1 else "false"
        ET.SubElement(settings, "helperBuySeeds").text = "true" if self._to_int(self._val("aiRefillSeeds"), 0) == 1 else "false"
        ET.SubElement(settings, "helperBuyFertilizer").text = "true" if self._to_int(self._val("aiRefillFertilizer"), 0) == 1 else "false"
        ET.SubElement(settings, "helperSlurrySource").text = str(self._to_int(self._val("aiRefillSlurry"), 0) + 1)
        ET.SubElement(settings, "helperManureSource").text = str(self._to_int(self._val("aiRefillManure"), 0) + 1)

        # Revision fields
        ET.SubElement(settings, "densityMapRevision").text = "4"
        ET.SubElement(settings, "terrainTextureRevision").text = "1"
        ET.SubElement(settings, "terrainLodTextureRevision").text = "2"
        ET.SubElement(settings, "splitShapesRevision").text = "2"
        ET.SubElement(settings, "tipCollisionRevision").text = "2"
        ET.SubElement(settings, "placementCollisionRevision").text = "2"
        ET.SubElement(settings, "navigationCollisionRevision").text = "2"

        ET.SubElement(settings, "mapDensityMapRevision").text = "1"
        ET.SubElement(settings, "mapTerrainTextureRevision").text = "1"
        ET.SubElement(settings, "mapTerrainLodTextureRevision").text = "1"
        ET.SubElement(settings, "mapSplitShapesRevision").text = "1"
        ET.SubElement(settings, "mapTipCollisionRevision").text = "1"
        ET.SubElement(settings, "mapPlacementCollisionRevision").text = "1"
        ET.SubElement(settings, "mapNavigationCollisionRevision").text = "1"

        disaster_val = self._to_int(self._val("disasterDestruction"), 0)
        disaster_map = {0: "OFF", 1: "VISUALS_ONLY", 2: "ENABLED"}
        ET.SubElement(settings, "disasterDestructionState").text = disaster_map.get(disaster_val, "OFF")

        ET.SubElement(settings, "dirtInterval").text = self._int_str("dirtInterval")

        ts_val = self._val("timeScale")
        if isinstance(ts_val, str):
            ts_num = TIMESCALE_MAP.get(ts_val, 5)
        else:
            ts_num = self._to_int(ts_val, 5)
        ET.SubElement(settings, "timeScale").text = f"{ts_num:.6f}"

        ET.SubElement(settings, "autoSaveInterval").text = f"{self._to_float(self._val('autoSaveInterval'), 0.0):.6f}"
        ET.SubElement(settings, "isCrossPlatformSavegame").text = "false"
        ET.SubElement(settings, "difficulty").text = "1"

        # Other sections
        map_node = ET.SubElement(root, "map")
        ET.SubElement(map_node, "foundHelpIcons").text = "00000000000000000000"
        init_help = ET.SubElement(root, "introductionHelp", active="false")
        ET.SubElement(init_help, "shownElements").text = ""
        ET.SubElement(init_help, "shownHints").text = ""

        stats = ET.SubElement(root, "statistics")
        ET.SubElement(stats, "money").text = str(self._to_int(self._val("money"), 0))
        ET.SubElement(stats, "playTime").text = "0.000000"

        split_shapes = ET.SubElement(root, "mapsSplitShapeFileIds", count="1")
        ET.SubElement(split_shapes, "id", id="0")

        ET.SubElement(root, "slotSystem", slotUsage="0")
        ET.SubElement(root, "foliageTypes").text = ""

        # Mods
        for mod in self._mods:
            mod_elem = ET.SubElement(root, "mod")
            mod_elem.set("modName", mod.get("modName", ""))
            mod_elem.set("title", mod.get("title", ""))
            mod_elem.set("version", mod.get("version", "1.0.0.0"))
            mod_elem.set("required", "true" if mod.get("id") == self._val("mapId") else "false")
            mod_elem.set("fileHash", "")

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        return tree

    def build_string(self) -> str:
        """Build XML and return as formatted string."""
        tree = self.build_tree()
        root = tree.getroot()
        if root is None:
            raise ValueError("XML root was not created")
        declaration = '<?xml version="1.0" encoding="utf-8" standalone="no"?>'
        xml_payload = ET.tostring(root, encoding="utf-8", short_empty_elements=False).decode("utf-8")
        return f"{declaration}\n{xml_payload}"

    def write(self, path: str):
        """Build XML and write to file."""
        xml_content = self.build_string()
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_content)
