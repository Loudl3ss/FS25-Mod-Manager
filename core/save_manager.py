import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.new_game_session import NewGameSession


@dataclass
class SaveInfo:
    slot: int
    path: str
    farm_name: str = ""
    map_title: str = ""
    money: float = 0.0
    play_time: float = 0.0        # hours
    save_date: str = ""
    game_version: str = ""
    exists: bool = False


class SaveManager:
    MAX_SLOTS = 20

    def __init__(self, base_path: str):
        self.base_path = base_path
        self.backup_dir = os.path.join(base_path, "backups_fs25manager")

    def get_all_saves(self) -> list[SaveInfo]:
        saves = []
        for slot in range(1, self.MAX_SLOTS + 1):
            saves.append(self.get_save(slot))
        # Only return slots that exist or first few empty ones
        existing = [s for s in saves if s.exists]
        empty = [s for s in saves if not s.exists][:3]
        return existing + empty

    def get_save(self, slot: int) -> SaveInfo:
        path = os.path.join(self.base_path, f"savegame{slot}")
        info = SaveInfo(slot=slot, path=path)
        info.exists = os.path.isdir(path)
        if info.exists:
            self._parse_save(info)
        return info

    def _parse_save(self, info: SaveInfo):
        xml_path = os.path.join(info.path, "careerSavegame.xml")
        if not os.path.exists(xml_path):
            info.farm_name = f"Save {info.slot}"
            return
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            settings = root.find("settings")
            if settings is None:
                settings = root

            def gt(tag, default=""):
                return (settings.findtext(tag) or "").strip() or default

            info.farm_name = gt("farmName") or gt("savegameName") or f"Save {info.slot}"
            info.map_title = gt("mapTitle") or gt("mapId") or "Unknown Map"
            info.save_date = gt("saveDateFormatted") or gt("creationDate") or ""
            info.game_version = gt("gameVersionNumber") or ""

            try:
                info.play_time = float(gt("playTime", "0"))
            except Exception:
                info.play_time = 0.0

            # Money from playerFarm element
            pf = root.find(".//playerFarm")
            if pf is not None:
                try:
                    info.money = float(pf.get("money", "0"))
                except Exception:
                    pass
            if info.money == 0:
                try:
                    info.money = float(gt("money", "0"))
                except Exception:
                    pass
        except Exception as e:
            print(f"Save parse error slot {info.slot}: {e}")
            info.farm_name = f"Save {info.slot}"

    def backup_save(self, slot: int) -> tuple[bool, str]:
        save_path = os.path.join(self.base_path, f"savegame{slot}")
        if not os.path.isdir(save_path):
            return False, "Save slot does not exist"
        os.makedirs(self.backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"savegame{slot}_{ts}.zip"
        zip_path = os.path.join(self.backup_dir, zip_name)
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root_dir, _, files in os.walk(save_path):
                    for file in files:
                        full = os.path.join(root_dir, file)
                        rel = os.path.relpath(full, save_path)
                        zf.write(full, rel)
            return True, zip_path
        except Exception as e:
            return False, str(e)

    def restore_save(self, zip_path: str, slot: int) -> tuple[bool, str]:
        save_path = os.path.join(self.base_path, f"savegame{slot}")
        try:
            if os.path.isdir(save_path):
                shutil.rmtree(save_path)
            os.makedirs(save_path, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(save_path)
            return True, "Restored successfully"
        except Exception as e:
            return False, str(e)

    def delete_save(self, slot: int) -> tuple[bool, str]:
        save_path = os.path.join(self.base_path, f"savegame{slot}")
        if not os.path.isdir(save_path):
            return False, "Save slot does not exist"
        try:
            shutil.rmtree(save_path)
            return True, "Deleted"
        except Exception as e:
            return False, str(e)

    def get_backups(self, slot: Optional[int] = None) -> list[str]:
        if not os.path.isdir(self.backup_dir):
            return []
        backups = []
        prefix = f"savegame{slot}_" if slot else "savegame"
        for f in sorted(os.listdir(self.backup_dir), reverse=True):
            if f.startswith(prefix) and f.endswith(".zip"):
                backups.append(os.path.join(self.backup_dir, f))
        return backups

    def delete_backup(self, zip_path: str) -> bool:
        try:
            os.remove(zip_path)
            return True
        except Exception:
            return False

    def finalize_new_game(self, session: NewGameSession) -> tuple[bool, str]:
        """
        Create a new game save with the given session data.
        
        Scans savegame1-savegame20 for the first empty slot, creates the directory,
        generates XML files with map and settings, and stores mod references.
        
        Args:
            session: NewGameSession containing selected_map, settings, and selected_mods
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not session.selected_map:
            return False, "No map selected"
        
        # Find first empty slot
        target_slot = None
        for slot in range(1, self.MAX_SLOTS + 1):
            save_path = os.path.join(self.base_path, f"savegame{slot}")
            career_xml = os.path.join(save_path, "careerSavegame.xml")
            
            # Slot is empty if directory doesn't exist or careerSavegame.xml doesn't exist
            if not os.path.isdir(save_path) or not os.path.exists(career_xml):
                target_slot = slot
                break
        
        if target_slot is None:
            return False, "All save slots are full"
        
        try:
            save_path = os.path.join(self.base_path, f"savegame{target_slot}")
            
            # Create directory
            os.makedirs(save_path, exist_ok=True)
            
            # Generate careerSavegame.xml
            career_xml_path = os.path.join(save_path, "careerSavegame.xml")
            self._generate_career_savegame_xml(
                career_xml_path,
                session.selected_map,
                session.settings,
                target_slot
            )
            
            # Generate placeables.xml
            placeables_xml_path = os.path.join(save_path, "placeables.xml")
            self._generate_placeables_xml(placeables_xml_path)
            
            # Store mod references as metadata
            if session.selected_mods:
                self._store_mod_references(save_path, session.selected_mods)
            
            return True, f"New game created in save slot {target_slot}"
        
        except Exception as e:
            # Cleanup on failure
            try:
                save_path = os.path.join(self.base_path, f"savegame{target_slot}")
                if os.path.isdir(save_path):
                    shutil.rmtree(save_path)
            except Exception:
                pass
            return False, f"Failed to create game: {str(e)}"

    def _generate_career_savegame_xml(self, xml_path: str, map_id: str, settings: dict, slot: int):
        """Generate a basic careerSavegame.xml file."""
        root = ET.Element("careerSavegame")
        
        # Settings
        settings_elem = ET.SubElement(root, "settings")
        ET.SubElement(settings_elem, "farmName").text = f"Farm {slot}"
        ET.SubElement(settings_elem, "savegameName").text = f"Save {slot}"
        ET.SubElement(settings_elem, "mapId").text = map_id
        ET.SubElement(settings_elem, "mapTitle").text = map_id
        ET.SubElement(settings_elem, "gameVersionNumber").text = "1.0.0"
        
        # Gameplay settings
        ET.SubElement(settings_elem, "difficulty").text = settings.get("difficulty", "Normal")
        ET.SubElement(settings_elem, "seasons").text = settings.get("seasons", "Enabled")
        ET.SubElement(settings_elem, "economicSystem").text = settings.get("economicSystem", "Realistic")
        
        # Initial values
        ET.SubElement(settings_elem, "playTime").text = "0"
        now = datetime.now()
        ET.SubElement(settings_elem, "saveDateFormatted").text = now.strftime("%Y-%m-%d %H:%M:%S")
        ET.SubElement(settings_elem, "creationDate").text = str(int(now.timestamp()))
        
        # Player farm element with starting money
        player_farm = ET.SubElement(root, "playerFarm")
        player_farm.set("money", "50000")  # Starting money
        
        # Write to file with pretty formatting
        tree = ET.ElementTree(root)
        self._indent_xml(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def _generate_placeables_xml(self, xml_path: str):
        """Generate a basic placeables.xml file."""
        root = ET.Element("placeables")
        
        # Empty placeables list - player will add their own
        placeables_list = ET.SubElement(root, "placeables")
        
        tree = ET.ElementTree(root)
        self._indent_xml(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def _store_mod_references(self, save_path: str, mod_names: list[str]):
        """Store enabled mods as metadata in the save directory."""
        mods_file = os.path.join(save_path, "mods.txt")
        with open(mods_file, "w") as f:
            for mod_name in mod_names:
                f.write(f"{mod_name}\n")

    @staticmethod
    def _indent_xml(elem, level=0):
        """Add pretty-printing indentation to XML tree."""
        indent_str = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent_str + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent_str
            for child in elem:
                SaveManager._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent_str
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent_str

