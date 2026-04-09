import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ModInfo:
    name: str
    filename: str
    filepath: str
    is_enabled: bool
    is_zip: bool
    title: str = ""
    author: str = ""
    version: str = ""
    description: str = ""
    icon_data: Optional[bytes] = None
    size_bytes: int = 0
    category: str = "Mod"
    id: str = ""  # Unique ID based on filename hash


class ModManager:
    def __init__(self, mods_path: str):
        self.mods_path = mods_path
        self.disabled_path = mods_path + "_disabled"
        self.thumbnails_path = mods_path + "_thumbnails"
        self.ensure_dirs()

    def ensure_dirs(self):
        os.makedirs(self.mods_path, exist_ok=True)
        os.makedirs(self.disabled_path, exist_ok=True)
        os.makedirs(self.thumbnails_path, exist_ok=True)

    def get_thumbnail_path(self, mod_id: str) -> str:
        """Get the file path for a mod's thumbnail."""
        return os.path.join(self.thumbnails_path, f"{mod_id}.png")

    def save_thumbnail(self, mod_id: str, icon_data: bytes) -> bool:
        """Save thumbnail data for a mod."""
        try:
            thumb_path = self.get_thumbnail_path(mod_id)
            with open(thumb_path, 'wb') as f:
                f.write(icon_data)
            return True
        except Exception:
            return False

    def load_thumbnail(self, mod_id: str) -> Optional[bytes]:
        """Load thumbnail data for a mod."""
        try:
            thumb_path = self.get_thumbnail_path(mod_id)
            if os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as f:
                    return f.read()
        except Exception:
            pass
        return None

    def cleanup_thumbnails(self, active_mod_ids: set[str]):
        """Remove thumbnails for mods that no longer exist."""
        try:
            for filename in os.listdir(self.thumbnails_path):
                if filename.endswith('.png'):
                    mod_id = filename[:-4]  # Remove .png extension
                    if mod_id not in active_mod_ids:
                        os.remove(os.path.join(self.thumbnails_path, filename))
        except Exception:
            pass

    def get_mods(self) -> list[ModInfo]:
        self.ensure_dirs()
        mods: list[ModInfo] = []
        active_mod_ids = set()
        
        for item in Path(self.mods_path).iterdir():
            if item.name.startswith("."):
                continue
            if item.suffix.lower() == ".zip" or item.is_dir():
                mod = self._parse_mod(str(item), is_enabled=True)
                if mod:
                    mods.append(mod)
                    active_mod_ids.add(mod.id)
                    
        disabled = Path(self.disabled_path)
        if disabled.exists():
            for item in disabled.iterdir():
                if item.name.startswith("."):
                    continue
                if item.suffix.lower() == ".zip" or item.is_dir():
                    mod = self._parse_mod(str(item), is_enabled=False)
                    if mod:
                        mods.append(mod)
                        active_mod_ids.add(mod.id)
        
        # Clean up thumbnails for removed mods
        self.cleanup_thumbnails(active_mod_ids)
        
        return sorted(mods, key=lambda m: (m.title or m.name).lower())

    def _parse_mod(self, filepath: str, is_enabled: bool) -> Optional[ModInfo]:
        path = Path(filepath)
        is_zip = path.suffix.lower() == ".zip"
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        
        # Generate unique ID based on filename
        mod_id = hashlib.md5(path.name.encode('utf-8')).hexdigest()[:16]
        
        mod = ModInfo(
            name=path.stem,
            filename=path.name,
            filepath=str(path),
            is_enabled=is_enabled,
            is_zip=is_zip,
            title=path.stem,
            size_bytes=size,
            id=mod_id,
        )
        
        # Try to load existing thumbnail first
        existing_thumb = self.load_thumbnail(mod_id)
        if existing_thumb:
            mod.icon_data = existing_thumb
        
        try:
            store_xml_path = None
            if is_zip:
                with zipfile.ZipFile(filepath, "r") as zf:
                    if "modDesc.xml" in zf.namelist():
                        with zf.open("modDesc.xml") as f:
                            store_xml_path = self._parse_mod_desc(mod, f.read())
                    
                    if store_xml_path and store_xml_path in zf.namelist():
                        with zf.open(store_xml_path) as f:
                            self._parse_store_item(mod, f.read())

                    icon_names = [
                        n for n in zf.namelist()
                        if "icon" in n.lower() and n.lower().endswith((".png", ".dds", ".jpg"))
                    ]
                    if icon_names:
                        try:
                            icon_bytes = zf.read(icon_names[0])
                            mod.icon_data = icon_bytes
                            # Save thumbnail if we don't have one or if it's different
                            if not existing_thumb or existing_thumb != icon_bytes:
                                self.save_thumbnail(mod_id, icon_bytes)
                        except Exception:
                            pass
            else:
                desc = path / "modDesc.xml"
                if desc.exists():
                    store_xml_path = self._parse_mod_desc(mod, desc.read_bytes())
                
                if store_xml_path:
                    store_xml_file = path / store_xml_path
                    if store_xml_file.exists():
                        self._parse_store_item(mod, store_xml_file.read_bytes())

                for icon_name in ["icon.png", "icon.dds", "modIcon.png"]:
                    icon_path = path / icon_name
                    if icon_path.exists():
                        try:
                            icon_bytes = icon_path.read_bytes()
                            mod.icon_data = icon_bytes
                            # Save thumbnail if we don't have one or if it's different
                            if not existing_thumb or existing_thumb != icon_bytes:
                                self.save_thumbnail(mod_id, icon_bytes)
                        except Exception:
                            pass
                        break
        except Exception:
            pass
        return mod

    def _parse_mod_desc(self, mod: ModInfo, data: bytes) -> Optional[str]:
        try:
            root = ET.fromstring(data)
            mod.author = (root.findtext("author") or "").strip()
            mod.version = (root.findtext("version") or "").strip()
            title_elem = root.find("title")
            if title_elem is not None:
                for lang in ["en", "de", "fr"]:
                    t = (title_elem.findtext(lang) or "").strip()
                    if t:
                        mod.title = t
                        break
                if not mod.title:
                    mod.title = (title_elem.text or "").strip() or mod.name
            desc_elem = root.find("description")
            if desc_elem is not None:
                for lang in ["en", "de", "fr"]:
                    d = (desc_elem.findtext(lang) or "").strip()
                    if d:
                        mod.description = d
                        break

            # Parse Category
            mod.category = "Mod"
            maps_node = root.find("maps")
            if maps_node is not None:
                for map_node in maps_node.findall("map"):
                    cfg = map_node.get("configFilename", "").lower()
                    if "map" in cfg and ".xml" in cfg:
                        mod.category = "Map"
                        return None
            
            # Find storeItem reference
            store_items = root.find("storeItems")
            if store_items is not None:
                first_item = store_items.find("storeItem")
                if first_item is not None:
                    return first_item.get("xmlFilename")
            
            # Fallback for scripts if no storeItems exist
            if root.find("type") is not None or root.find("types") is not None or "script" in (mod.title or "").lower():
                mod.category = "Script"

        except Exception:
            pass
        return None

    def _parse_store_item(self, mod: ModInfo, data: bytes):
        try:
            root = ET.fromstring(data)
            store_data = root.find("storeData")
            if store_data is not None:
                cat = store_data.findtext("category")
                if cat:
                    cat = cat.strip()
                    mapping = {
                        "tractorsmedium": "Medium Tractor",
                        "tractorssmall": "Small Tractor",
                        "tractorslarge": "Large Tractor",
                        "sprayers": "Sprayer",
                        "mowers": "Mower",
                        "balers": "Baler",
                        "trailers": "Trailer",
                        "trucks": "Truck",
                        "loaders": "Loader",
                        "weights": "Weight",
                        "seeders": "Seeder",
                        "plows": "Plow",
                        "cultivators": "Cultivator",
                        "frontloaders": "Front Loader",
                        "placeable": "Placeable",
                        "sheds": "Shed",
                        "silos": "Silo",
                        "factories": "Factory",
                        "animals": "Animal Pen"
                    }
                    lower_cat = cat.lower()
                    if lower_cat in mapping:
                        mod.category = mapping[lower_cat]
                    else:
                        import re
                        s = re.sub('([A-Z])', r' \1', cat)
                        mod.category = " ".join([word.capitalize() for word in s.split()])
        except Exception:
            pass

    def enable_mod(self, mod: ModInfo) -> bool:
        try:
            dest = os.path.join(self.mods_path, mod.filename)
            shutil.move(mod.filepath, dest)
            mod.filepath = dest
            mod.is_enabled = True
            return True
        except Exception as e:
            print(f"Enable error: {e}")
            return False

    def disable_mod(self, mod: ModInfo) -> bool:
        try:
            os.makedirs(self.disabled_path, exist_ok=True)
            dest = os.path.join(self.disabled_path, mod.filename)
            shutil.move(mod.filepath, dest)
            mod.filepath = dest
            mod.is_enabled = False
            return True
        except Exception as e:
            print(f"Disable error: {e}")
            return False

    def delete_mod(self, mod: ModInfo) -> bool:
        try:
            p = Path(mod.filepath)
            if p.is_dir():
                shutil.rmtree(str(p))
            else:
                p.unlink()
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False

    def open_folder(self):
        subprocess.Popen(["xdg-open", self.mods_path])

    def stats(self) -> dict:
        mods = self.get_mods()
        enabled = sum(1 for m in mods if m.is_enabled)
        total_size = sum(m.size_bytes for m in mods)
        return {
            "total": len(mods),
            "enabled": enabled,
            "disabled": len(mods) - enabled,
            "size_mb": round(total_size / (1024 * 1024), 1),
        }
