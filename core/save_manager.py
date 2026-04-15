import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.new_game_session import NewGameSession
from core.xml_generator import CareerXmlBuilder


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


@dataclass
class BackupInfo:
    path: str
    filename: str
    is_auto: bool

    @property
    def display_name(self) -> str:
        prefix = "[Auto Backup]" if self.is_auto else "[App Backup]"
        return f"{prefix} {self.filename}"


class SaveManager:
    MAX_SLOTS = 20

    def __init__(self, base_path: str, backup_dir: Optional[str] = None, default_backup_base: Optional[str] = None):
        self.base_path = base_path
        backup_base = default_backup_base or base_path
        self.default_backup_dir = os.path.join(backup_base, "backups_fs25manager")
        self.backup_dir = backup_dir or self.default_backup_dir
        self.official_backup_dir = os.path.join(base_path, "savegameBackup")

    def set_backup_dir(self, backup_dir: Optional[str]):
        path = (backup_dir or "").strip()
        self.backup_dir = path or self.default_backup_dir

    def set_default_backup_base(self, backup_base: str):
        self.default_backup_dir = os.path.join(backup_base, "backups_fs25manager")

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

            info.play_time = self._safe_float(gt("playTime", "0"), default=0.0)

            # Money from playerFarm element
            pf = root.find(".//playerFarm")
            if pf is not None:
                info.money = self._safe_float(pf.get("money", "0"), default=0.0)
            if info.money == 0:
                info.money = self._safe_float(gt("money", "0"), default=0.0)
        except Exception as e:
            print(f"Save parse error slot {info.slot}: {e}")
            info.farm_name = f"Save {info.slot}"

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _cleanup_partial_save(self, slot: int | None) -> None:
        if slot is None:
            return
        try:
            save_path = os.path.join(self.base_path, f"savegame{slot}")
            if os.path.isdir(save_path):
                shutil.rmtree(save_path)
        except Exception:
            # Best-effort cleanup should never mask original error.
            pass

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

    def restore_save(self, path: str, slot: int) -> tuple[bool, str]:
        save_path = os.path.join(self.base_path, f"savegame{slot}")
        try:
            if os.path.isdir(save_path):
                shutil.rmtree(save_path)
            os.makedirs(save_path, exist_ok=True)

            if os.path.isfile(path) and path.endswith(".zip"):
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(save_path)
            elif os.path.isdir(path):
                shutil.copytree(path, save_path, dirs_exist_ok=True)
            else:
                return False, "Unsupported backup format or path does not exist."

            return True, "Restored successfully"
        except Exception as e:
            return False, str(e)

    def delete_save(self, slot: int) -> tuple[bool, str]:
        save_path = os.path.join(self.base_path, f"savegame{slot}")
        if not os.path.isdir(save_path):
            return False, "Save slot does not exist"
        try:
            for entry in os.scandir(save_path):
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)
            return True, "Deleted"
        except Exception as e:
            return False, str(e)

    def copy_save(self, src_slot: int, dst_slot: int) -> tuple[bool, str]:
        if src_slot == dst_slot:
            return False, "Source and destination slots are the same"
        src_path = os.path.join(self.base_path, f"savegame{src_slot}")
        dst_path = os.path.join(self.base_path, f"savegame{dst_slot}")
        if not os.path.isdir(src_path):
            return False, "Source save slot does not exist"
        try:
            if os.path.isdir(dst_path):
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            return True, f"Copied to Slot {dst_slot}"
        except Exception as e:
            return False, str(e)

    def get_backups(self, slot: Optional[int] = None) -> list[BackupInfo]:
        backups: list[BackupInfo] = []
        prefix = f"savegame{slot}_" if slot else "savegame"

        # 1) App zip backups
        if os.path.isdir(self.backup_dir):
            for f in os.listdir(self.backup_dir):
                if f.startswith(prefix) and f.endswith(".zip"):
                    backups.append(
                        BackupInfo(
                            path=os.path.join(self.backup_dir, f),
                            filename=f,
                            is_auto=False,
                        )
                    )

        # 2) Official game folder backups
        if os.path.isdir(self.official_backup_dir):
            for f in os.listdir(self.official_backup_dir):
                full_path = os.path.join(self.official_backup_dir, f)
                if f.startswith(prefix) and os.path.isdir(full_path):
                    backups.append(
                        BackupInfo(
                            path=full_path,
                            filename=f,
                            is_auto=True,
                        )
                    )

        return sorted(backups, key=lambda b: b.filename, reverse=True)

    def delete_backup(self, path: str) -> bool:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True
        except Exception:
            return False

    def finalize_new_game(self, session: NewGameSession, mod_manager=None) -> tuple[bool, str]:
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
        
        # Find first reusable slot.
        # Prefer an existing savegame folder that has no careerSavegame.xml,
        # then fall back to the first missing savegame folder.
        target_slot = None
        first_missing_slot = None
        for slot in range(1, self.MAX_SLOTS + 1):
            save_path = os.path.join(self.base_path, f"savegame{slot}")
            career_xml = os.path.join(save_path, "careerSavegame.xml")

            if os.path.isdir(save_path) and not os.path.exists(career_xml):
                target_slot = slot
                break

            if not os.path.isdir(save_path) and first_missing_slot is None:
                first_missing_slot = slot

        if target_slot is None:
            target_slot = first_missing_slot

        if target_slot is None:
            return False, "All save slots are full"
        
        try:
            save_path = os.path.join(self.base_path, f"savegame{target_slot}")
            
            # Create directory
            os.makedirs(save_path, exist_ok=True)
            
            # Resolve map and selected mod details if manager is available.
            mod_objs: list[dict[str, str]] = []
            final_map_id = session.selected_map
            final_map_title = session.selected_map

            if mod_manager:
                all_mods = {m.id: m for m in mod_manager.get_mods()}

                if session.selected_map in all_mods:
                    map_mod = all_mods[session.selected_map]
                    stem_name = Path(map_mod.filename).stem if map_mod.filename else map_mod.name
                    final_map_id = stem_name or map_mod.name or session.selected_map
                    final_map_title = map_mod.title or map_mod.name or final_map_id

                    # Ensure map mod is present in XML mod list.
                    mod_objs.append(
                        {
                            "id": final_map_id,
                            "modName": map_mod.name,
                            "title": map_mod.title or map_mod.name,
                            "version": map_mod.version or "1.0.0.0",
                        }
                    )

                for mod_id in session.selected_mods:
                    if mod_id in all_mods:
                        m = all_mods[mod_id]
                        mod_objs.append(
                            {
                                "id": m.id,
                                "modName": m.name,
                                "title": m.title or m.name,
                                "version": m.version or "1.0.0.0",
                            }
                        )

            # De-duplicate in case selected mods include map-like entries.
            dedup: dict[str, dict[str, str]] = {}
            for mod in mod_objs:
                dedup[mod.get("modName", "")] = mod
            mod_objs = list(dedup.values())

            # Generate careerSavegame.xml
            career_xml_path = os.path.join(save_path, "careerSavegame.xml")
            self._generate_career_savegame_xml(
                career_xml_path,
                final_map_id,
                final_map_title,
                session.settings,
                target_slot,
                mod_objs,
            )
            
            # Generate placeables.xml
            placeables_xml_path = os.path.join(save_path, "placeables.xml")
            self._generate_placeables_xml(placeables_xml_path)
            
            # Keep a plain list as metadata for quick debug/inspection.
            if session.selected_mods:
                self._store_mod_references(save_path, session.selected_mods)
            
            return True, f"New game created in save slot {target_slot}"
        
        except Exception as e:
            self._cleanup_partial_save(target_slot)
            return False, f"Failed to create game: {str(e)}"

    def _generate_career_savegame_xml(
        self,
        xml_path: str,
        map_id: str,
        map_title: str,
        settings: dict,
        slot: int,
        mods: list[dict[str, str]] | None = None,
    ):
        """Generate careerSavegame.xml using CareerXmlBuilder."""
        build_settings = dict(settings)
        build_settings["mapId"] = map_id
        build_settings["mapTitle"] = build_settings.get("mapTitle") or map_title or map_id
        if not build_settings.get("farmName"):
            build_settings["farmName"] = f"Farm {slot}"

        builder = CareerXmlBuilder(build_settings, mods=mods or [])
        builder.write(xml_path)

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
        with open(mods_file, "w", encoding="utf-8") as f:
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

