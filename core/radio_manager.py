from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


class RadioManager:
    """Manage in-game radio stations and local music folder linkage."""

    SUPPORTED_LOCAL_FORMATS = {".mp3", ".flac", ".ogg", ".wav"}

    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)

    def _load_tree(self):
        if self.xml_path.exists():
            try:
                tree = ET.parse(self.xml_path)
                root = tree.getroot()
                if root.tag == "streamingInternetRadios":
                    return tree
            except ET.ParseError:
                pass

        root = ET.Element("streamingInternetRadios")
        return ET.ElementTree(root)

    def _root(self, tree) -> ET.Element:
        root = tree.getroot()
        if root is None:
            root = ET.Element("streamingInternetRadios")
            tree._setroot(root)
        return root

    def _safe_write(self, tree):
        self.xml_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix="streamingInternetRadios_",
            suffix=".xml",
            dir=str(self.xml_path.parent),
        )
        try:
            os.close(fd)
            tree.write(tmp_path, encoding="utf-8", xml_declaration=True)
            os.replace(tmp_path, self.xml_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get_web_stations(self) -> list[str]:
        tree = self._load_tree()
        root = self._root(tree)
        stations: list[str] = []
        for node in list(root):
            if node.tag != "streamingInternetRadio":
                continue
            href = (node.get("href") or "").strip()
            if href:
                stations.append(href)
        return stations

    def add_web_station(self, url: str) -> bool:
        clean_url = (url or "").strip()
        if not clean_url:
            return False

        tree = self._load_tree()
        root = self._root(tree)
        existing = {
            (node.get("href") or "").strip()
            for node in list(root)
            if node.tag == "streamingInternetRadio"
        }
        if clean_url in existing:
            return False

        # ET.SubElement appends as the last child, which keeps user-added radios at the end.
        ET.SubElement(root, "streamingInternetRadio", {"href": clean_url})
        self._safe_write(tree)
        return True

    def remove_web_station(self, url: str) -> bool:
        clean_url = (url or "").strip()
        if not clean_url:
            return False

        tree = self._load_tree()
        root = self._root(tree)
        removed = False
        for node in list(root):
            if node.tag != "streamingInternetRadio":
                continue
            href = (node.get("href") or "").strip()
            if href == clean_url:
                root.remove(node)
                removed = True
                break

        if removed:
            self._safe_write(tree)
        return removed

    def has_supported_music_files(self, source_folder: str) -> bool:
        path = Path(source_folder)
        if not path.is_dir():
            return False

        for file in path.rglob("*"):
            if file.is_file() and file.suffix.lower() in self.SUPPORTED_LOCAL_FORMATS:
                return True
        return False

    def get_linked_music_folder(self, target_music_folder: str) -> str:
        target = Path(target_music_folder)
        if target.is_symlink():
            try:
                return str(target.resolve())
            except Exception:
                return str(target)
        if target.exists() and target.is_dir():
            return str(target)
        return ""

    def link_local_music_folder(self, source_folder: str, target_music_folder: str) -> tuple[bool, str]:
        source = Path(source_folder).expanduser()
        target = Path(target_music_folder).expanduser()

        if not source.is_dir():
            return False, "Selected source folder does not exist."

        if not self.has_supported_music_files(str(source)):
            return False, "Folder does not contain supported music files (MP3/FLAC/OGG/WAV)."

        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.exists() and target.is_dir():
                if any(target.iterdir()):
                    return False, "Target music folder exists and is not empty."
                target.rmdir()

            os.symlink(str(source), str(target))
            return True, f"Linked {source} -> {target}"
        except OSError as exc:
            return False, str(exc)
