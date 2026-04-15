import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.logging_utils import get_logger


logger = get_logger("settings")


@dataclass
class GameSettings:
    # Difficulty
    difficulty: int = 2          # 1=Easy 2=Normal 3=Hard
    economy_difficulty: int = 2  # 1=Easy 2=Normal 3=Hard
    # Economy
    loan_interest_rate: float = 6.0    # percent
    price_change_range: float = 0.2    # 0.0–1.0
    # Vehicle / Realism
    fuel_usage: int = 2          # 1=Low 2=Medium 3=Realistic
    dirt_interval: int = 2       # 1=Off 2=Normal 3=Realistic
    vehicle_damage_age: int = 2  # 1=Off 2=Normal 3=Realistic
    # Flags
    plowing_required: bool = False
    stones_enabled: bool = False
    weeds_enabled: bool = False
    lime_required: bool = False
    snow_enabled: bool = True

    _path: str = field(default="", repr=False)

    def copy(self) -> "GameSettings":
        import copy
        return copy.copy(self)


DIFF_MAP = {1: "Easy", 2: "Normal", 3: "Hard"}
REALISM_MAP = {1: "Off / Low", 2: "Normal", 3: "Realistic"}
FUEL_MAP = {1: "Low", 2: "Normal", 3: "High"}


class SettingsManager:
    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def _parse_int(value: str | None, default: int) -> int:
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_float(value: str | None, default: float) -> float:
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes")

    def load(self) -> GameSettings:
        s = GameSettings(_path=self.path)
        p = Path(self.path)
        if not p.exists():
            return s
        try:
            tree = ET.parse(str(p))
            root = tree.getroot()

            s.difficulty = self._parse_int(root.findtext("difficulty"), 2)
            s.economy_difficulty = self._parse_int(root.findtext("economyDifficulty"), 2)
            s.loan_interest_rate = self._parse_float(root.findtext("loanAnnualInterestRate"), 6.0)
            s.price_change_range = self._parse_float(root.findtext("priceChangeRange"), 0.2)
            s.fuel_usage = self._parse_int(root.findtext("fuelUsage"), 2)
            s.dirt_interval = self._parse_int(root.findtext("dirtInterval"), 2)
            s.vehicle_damage_age = self._parse_int(root.findtext("vehicleDamageAge"), 2)
            s.plowing_required = self._parse_bool(root.findtext("plowingRequiredEnabled"), False)
            s.stones_enabled = self._parse_bool(root.findtext("stoneEnabled"), False)
            s.weeds_enabled = self._parse_bool(root.findtext("weedsEnabled"), False)
            s.lime_required = self._parse_bool(root.findtext("limeRequired"), False)
            s.snow_enabled = self._parse_bool(root.findtext("isSnowEnabled"), True)
        except (ET.ParseError, OSError, TypeError, ValueError) as e:
            logger.warning("Settings load error: %s", e)
        return s

    def save(self, s: GameSettings) -> bool:
        p = Path(self.path)
        try:
            if p.exists():
                tree = ET.parse(str(p))
                root = tree.getroot()
            else:
                root = ET.Element("gameSettings")
                tree = ET.ElementTree(root)

            def set_tag(tag, value):
                elem = root.find(tag)
                if elem is None:
                    elem = ET.SubElement(root, tag)
                elem.text = str(value)

            set_tag("difficulty", s.difficulty)
            set_tag("economyDifficulty", s.economy_difficulty)
            set_tag("loanAnnualInterestRate", s.loan_interest_rate)
            set_tag("priceChangeRange", s.price_change_range)
            set_tag("fuelUsage", s.fuel_usage)
            set_tag("dirtInterval", s.dirt_interval)
            set_tag("vehicleDamageAge", s.vehicle_damage_age)
            set_tag("plowingRequiredEnabled", str(s.plowing_required).lower())
            set_tag("stoneEnabled", str(s.stones_enabled).lower())
            set_tag("weedsEnabled", str(s.weeds_enabled).lower())
            set_tag("limeRequired", str(s.lime_required).lower())
            set_tag("isSnowEnabled", str(s.snow_enabled).lower())

            ET.indent(tree, space="    ")
            tree.write(str(p), encoding="utf-8", xml_declaration=True)
            return True
        except (ET.ParseError, OSError, TypeError, ValueError) as e:
            logger.warning("Settings save error: %s", e)
            return False
