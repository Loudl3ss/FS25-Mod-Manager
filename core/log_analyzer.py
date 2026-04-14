from __future__ import annotations

import os
import re
from pathlib import Path


class LogAnalyzer:
    """Parse and categorize FS25 log entries."""

    DEFAULT_LOG_FILENAME = "log.txt"
    # Optional fallback path used only when configured log path is missing.
    STATIC_BAZZITE_LOG_PATH = os.path.expanduser(
        "~/.steam/steam/steamapps/compatdata/2243200/pfx/drive_c/users/steamuser/Documents/My Games/FarmingSimulator2025/log.txt"
    )

    # Pattern dictionary inspired by your reference implementation.
    ERROR_DICTIONARY = [
        {
            "pattern": re.compile(r"Error: Invalid mod name '(.+?)'!", re.IGNORECASE),
            "human_title": "Invalid Mod File Name",
            "human_msg": "Invalid mod file name: {0}",
            "action": "Rename the ZIP file. The name cannot contain spaces, leading numbers, or special characters (use only letters and underscores '_').",
        },
        {
            "pattern": re.compile(r"Error: Unsupported mod description version in mod (.+)", re.IGNORECASE),
            "human_title": "Unsupported Mod Version",
            "human_msg": "Mod '{0}' is designed for an older game version (FS19 or FS22).",
            "action": "Delete this file. FS25 does not support old mods without manual conversion.",
        },
        {
            "pattern": re.compile(r"Error: Failed to open xml file '(.+?)'", re.IGNORECASE),
            "human_title": "Corrupted XML File",
            "human_msg": "Corrupted file: Failed to open XML ({0}).",
            "action": "The mod files are damaged or were extracted incorrectly. Re-download the mod.",
        },
        {
            "pattern": re.compile(r"Error: Missing dds file '(.+?)'", re.IGNORECASE),
            "human_title": "Missing Texture",
            "human_msg": "Missing texture file: {0}",
            "action": "The mod creator forgot to include the image in the ZIP file, or the archive is corrupted. This might cause game crashes.",
        },
        {
            "pattern": re.compile(r"Warning: Duplicate lua script '(.+?)'", re.IGNORECASE),
            "human_title": "Duplicate LUA Script",
            "human_msg": "Script conflict: Multiple mods are trying to load the same script '{0}'.",
            "action": "This often happens when using multiple GPS, Autoload, or economy mods simultaneously. Keep only one.",
        },
        {
            "pattern": re.compile(r"Error: Running LUA method '(.+?)'", re.IGNORECASE),
            "human_title": "LUA Runtime Crash",
            "human_msg": "Critical script crash (LUA method '{0}' failed).",
            "action": "A mod has encountered a fatal error. Check the raw log lines below to identify the faulty mod and remove it.",
        },
        {
            "pattern": re.compile(r"Warning: Shape from '(.+?)' too big", re.IGNORECASE),
            "human_title": "Oversized 3D Model",
            "human_msg": "Mod '{0}' is poorly optimized (3D model is excessively large).",
            "action": "The game will still run, but this mod will significantly reduce your FPS. Use at your own discretion.",
        },
        {
            "pattern": re.compile(r"Error: Out of memory", re.IGNORECASE),
            "human_title": "Out of Memory",
            "human_msg": "System ran out of Random Access Memory (RAM) or Video Memory (VRAM).",
            "action": "The game is overloaded with too many mods or high-resolution textures. Delete unnecessary mods or lower your graphics settings.",
        },
        {
            "pattern": re.compile(
                r"(?:corrupt|invalid).*(?:zip|archive)|(?:zip|archive).*(?:corrupt|invalid)|not a zip archive",
                re.IGNORECASE,
            ),
            "human_title": "Corrupt ZIP Archive",
            "human_msg": "Archive appears corrupt or invalid.",
            "action": "Re-download the mod archive and verify it opens correctly before installing.",
        },
    ]

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.log_path = self.base_path / self.DEFAULT_LOG_FILENAME

    def _resolve_log_path(self) -> Path:
        if self.log_path.exists() and self.log_path.is_file():
            return self.log_path

        fallback = Path(self.STATIC_BAZZITE_LOG_PATH)
        if fallback.exists() and fallback.is_file():
            return fallback

        return self.log_path

    def _translate_line(self, raw_line: str) -> dict[str, str]:
        issue_type = "ERROR" if ("Error:" in raw_line or "Exception:" in raw_line) else "WARNING"

        for rule in self.ERROR_DICTIONARY:
            match = rule["pattern"].search(raw_line)
            if match:
                extracted = ""
                if match.groups():
                    extracted = match.group(1)

                human_msg = rule["human_msg"].format(extracted)
                return {
                    "type": issue_type,
                    "human_title": rule["human_title"],
                    "human_action": rule["action"],
                    "raw_line": raw_line.strip(),
                    # Compatibility with the requested schema wording.
                    "human_msg": human_msg,
                    "raw": raw_line.strip(),
                }

        return {
            "type": issue_type,
            "human_title": "Unknown Error",
            "human_action": "Review the raw log line below for technical details.",
            "raw_line": raw_line.strip(),
            # Compatibility with the requested schema wording.
            "human_msg": "Unknown Error or Warning detected.",
            "raw": raw_line.strip(),
        }

    def parse_log(self) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []

        source_log_path = self._resolve_log_path()
        if not source_log_path.exists() or not source_log_path.is_file():
            return entries

        try:
            with open(source_log_path, "r", encoding="utf-8", errors="replace") as handle:
                for raw_line in handle:
                    line = raw_line.rstrip("\n\r")

                    if "Error:" in line or "Warning:" in line or "Exception:" in line:
                        translated = self._translate_line(line)
                        entries.append(translated)
                    else:
                        entries.append(
                            {
                                "type": "INFO",
                                "human_title": "Info",
                                "human_action": "No action required.",
                                "raw_line": line,
                                "human_msg": "Info",
                                "raw": line,
                            }
                        )
        except Exception:
            return [
                {
                    "type": "ERROR",
                    "human_title": "Analyzer Failure",
                    "human_action": "Verify file permissions and ensure the game is not locking the file.",
                    "raw_line": "Could not read log.txt",
                    "human_msg": "Analyzer Failure: Could not read log.txt.",
                    "raw": "Could not read log.txt",
                }
            ]

        return entries
