import hashlib
import os
import shutil
import sqlite3
import subprocess
import time
import zipfile
import xml.etree.ElementTree as ET
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
    thumbnail_id: str = ""


class ModManager:
    def __init__(self, mods_path: str, app_cache_root: Optional[str] = None):
        self.mods_path = mods_path
        cache_root = Path(app_cache_root).expanduser() if app_cache_root else Path(mods_path).parent
        self.cache_path = str(cache_root / "mods_cache")
        self.thumbnails_path = os.path.join(self.cache_path, "thumbnails")
        self.thumbnail_db_path = os.path.join(self.cache_path, "thumbnail_cache.sqlite3")
        self.ensure_dirs()

    def ensure_dirs(self):
        os.makedirs(self.mods_path, exist_ok=True)
        os.makedirs(self.cache_path, exist_ok=True)
        os.makedirs(self.thumbnails_path, exist_ok=True)
        self._ensure_thumbnail_db()

    def _ensure_thumbnail_db(self):
        with sqlite3.connect(self.thumbnail_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thumbnail_cache (
                    mod_id TEXT PRIMARY KEY,
                    thumbnail_id TEXT NOT NULL,
                    mod_filename TEXT NOT NULL,
                    mod_path TEXT NOT NULL,
                    cache_filename TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def get_thumbnail_path(self, thumbnail_id: str) -> str:
        """Get the file path for a cached thumbnail."""
        return os.path.join(self.thumbnails_path, f"{thumbnail_id}.bin")

    def _get_thumbnail_record(self, mod_id: str) -> Optional[sqlite3.Row]:
        try:
            with sqlite3.connect(self.thumbnail_db_path) as conn:
                conn.row_factory = sqlite3.Row
                return conn.execute(
                    "SELECT * FROM thumbnail_cache WHERE mod_id = ?",
                    (mod_id,),
                ).fetchone()
        except Exception:
            return None

    def save_thumbnail(self, mod: ModInfo, icon_data: bytes) -> str:
        """Save thumbnail data for a mod and index it in the cache database."""
        try:
            thumbnail_id = hashlib.sha1(icon_data).hexdigest()[:24]
            thumb_path = self.get_thumbnail_path(thumbnail_id)

            if not os.path.exists(thumb_path):
                with open(thumb_path, "wb") as handle:
                    handle.write(icon_data)

            with sqlite3.connect(self.thumbnail_db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO thumbnail_cache (
                        mod_id, thumbnail_id, mod_filename, mod_path, cache_filename, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(mod_id) DO UPDATE SET
                        thumbnail_id = excluded.thumbnail_id,
                        mod_filename = excluded.mod_filename,
                        mod_path = excluded.mod_path,
                        cache_filename = excluded.cache_filename,
                        updated_at = excluded.updated_at
                    """,
                    (
                        mod.id,
                        thumbnail_id,
                        mod.filename,
                        mod.filepath,
                        os.path.basename(thumb_path),
                        time.time(),
                    ),
                )
                conn.commit()

            mod.thumbnail_id = thumbnail_id
            return thumbnail_id
        except Exception:
            return ""

    def load_thumbnail(self, mod_id: str) -> tuple[Optional[bytes], str]:
        """Load thumbnail data and its thumbnail ID for a mod."""
        try:
            record = self._get_thumbnail_record(mod_id)
            if not record:
                return None, ""

            thumb_path = os.path.join(self.thumbnails_path, record["cache_filename"])
            if not os.path.exists(thumb_path):
                with sqlite3.connect(self.thumbnail_db_path) as conn:
                    conn.execute("DELETE FROM thumbnail_cache WHERE mod_id = ?", (mod_id,))
                    conn.commit()
                return None, ""

            with open(thumb_path, "rb") as handle:
                return handle.read(), record["thumbnail_id"]
        except Exception:
            return None, ""

    def cleanup_thumbnails(self, active_mod_ids: set[str]):
        """Remove cached thumbnails and index entries for mods that no longer exist."""
        try:
            with sqlite3.connect(self.thumbnail_db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT mod_id, cache_filename FROM thumbnail_cache"
                ).fetchall()

                stale_mod_ids = [row["mod_id"] for row in rows if row["mod_id"] not in active_mod_ids]
                if stale_mod_ids:
                    conn.executemany(
                        "DELETE FROM thumbnail_cache WHERE mod_id = ?",
                        [(mod_id,) for mod_id in stale_mod_ids],
                    )
                    conn.commit()

                referenced_files = {
                    row["cache_filename"]
                    for row in conn.execute("SELECT cache_filename FROM thumbnail_cache").fetchall()
                }

            for filename in os.listdir(self.thumbnails_path):
                if filename not in referenced_files:
                    os.remove(os.path.join(self.thumbnails_path, filename))
        except Exception:
            pass

    def sync_thumbnail_cache(self, active_mod_ids: set[str]):
        """Sync cache index and files against the current contents of the mods folders."""
        self.cleanup_thumbnails(active_mod_ids)

    def get_mods(self) -> list[ModInfo]:
        self.ensure_dirs()
        mods: list[ModInfo] = []
        active_mod_ids = set()

        for item in Path(self.mods_path).iterdir():
            if item.name.startswith("."):
                continue
            if item.suffix.lower() == ".zip" or item.is_dir():
                mod = self._parse_mod(str(item))
                if mod:
                    mods.append(mod)
                    active_mod_ids.add(mod.id)

        self.sync_thumbnail_cache(active_mod_ids)
        return sorted(mods, key=lambda mod: (mod.title or mod.name).lower())

    def _parse_mod(self, filepath: str) -> Optional[ModInfo]:
        path = Path(filepath)
        is_zip = path.suffix.lower() == ".zip"
        try:
            size = path.stat().st_size
        except Exception:
            size = 0

        mod_id = hashlib.md5(path.name.encode("utf-8")).hexdigest()[:16]

        mod = ModInfo(
            name=path.stem,
            filename=path.name,
            filepath=str(path),
            is_enabled=True,
            is_zip=is_zip,
            title=path.stem,
            size_bytes=size,
            id=mod_id,
        )

        existing_thumb, existing_thumbnail_id = self.load_thumbnail(mod_id)
        if existing_thumb:
            mod.icon_data = existing_thumb
            mod.thumbnail_id = existing_thumbnail_id

        try:
            store_xml_path = None
            if is_zip:
                with zipfile.ZipFile(filepath, "r") as archive:
                    if "modDesc.xml" in archive.namelist():
                        with archive.open("modDesc.xml") as handle:
                            store_xml_path = self._parse_mod_desc(mod, handle.read())

                    if store_xml_path and store_xml_path in archive.namelist():
                        with archive.open(store_xml_path) as handle:
                            self._parse_store_item(mod, handle.read())

                    icon_names = [
                        name
                        for name in archive.namelist()
                        if "icon" in name.lower() and name.lower().endswith((".svg", ".dds", ".jpg", ".jpeg"))
                    ]
                    if icon_names:
                        try:
                            icon_bytes = archive.read(icon_names[0])
                            mod.icon_data = icon_bytes
                            if not existing_thumb or existing_thumb != icon_bytes:
                                mod.thumbnail_id = self.save_thumbnail(mod, icon_bytes)
                            elif existing_thumbnail_id:
                                mod.thumbnail_id = existing_thumbnail_id
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

                for icon_name in ["icon.svg", "icon.dds", "modIcon.svg"]:
                    icon_path = path / icon_name
                    if icon_path.exists():
                        try:
                            icon_bytes = icon_path.read_bytes()
                            mod.icon_data = icon_bytes
                            if not existing_thumb or existing_thumb != icon_bytes:
                                mod.thumbnail_id = self.save_thumbnail(mod, icon_bytes)
                            elif existing_thumbnail_id:
                                mod.thumbnail_id = existing_thumbnail_id
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
                    text = (title_elem.findtext(lang) or "").strip()
                    if text:
                        mod.title = text
                        break
                if not mod.title:
                    mod.title = (title_elem.text or "").strip() or mod.name
            desc_elem = root.find("description")
            if desc_elem is not None:
                for lang in ["en", "de", "fr"]:
                    text = (desc_elem.findtext(lang) or "").strip()
                    if text:
                        mod.description = text
                        break

            mod.category = "Mod"
            maps_node = root.find("maps")
            if maps_node is not None:
                for map_node in maps_node.findall("map"):
                    cfg = map_node.get("configFilename", "").lower()
                    if "map" in cfg and ".xml" in cfg:
                        mod.category = "Map"
                        return None

            store_items = root.find("storeItems")
            if store_items is not None:
                first_item = store_items.find("storeItem")
                if first_item is not None:
                    return first_item.get("xmlFilename")

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
                        "animals": "Animal Pen",
                    }
                    lower_cat = cat.lower()
                    if lower_cat in mapping:
                        mod.category = mapping[lower_cat]
                    else:
                        import re

                        spaced = re.sub(r"([A-Z])", r" \1", cat)
                        mod.category = " ".join(word.capitalize() for word in spaced.split())
        except Exception:
            pass

    def delete_mod(self, mod: ModInfo) -> bool:
        try:
            path = Path(mod.filepath)
            if path.is_dir():
                shutil.rmtree(str(path))
            else:
                path.unlink()
            return True
        except Exception as exc:
            print(f"Delete error: {exc}")
            return False

    def open_folder(self):
        subprocess.Popen(["xdg-open", self.mods_path])

    def stats(self) -> dict:
        mods = self.get_mods()
        total_size = sum(mod.size_bytes for mod in mods)
        return {
            "total": len(mods),
            "size_mb": round(total_size / (1024 * 1024), 1),
        }
