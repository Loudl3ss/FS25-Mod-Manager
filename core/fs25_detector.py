import os
from pathlib import Path


class FS25Detector:
    """Detects Farming Simulator 25 user data path on Linux."""

    COMMON_PATHS = [
        "~/FarmingSimulator2025",
        "~/Documents/My Games/FarmingSimulator2025",
        "~/.local/share/FarmingSimulator2025",
        "~/snap/FarmingSimulator2025",
    ]

    @staticmethod
    def find_user_data_path() -> str | None:
        for pattern in FS25Detector.COMMON_PATHS:
            path = Path(pattern).expanduser()
            if path.exists() and path.is_dir():
                return str(path)
        return None

    @staticmethod
    def validate_path(path: str) -> bool:
        if not path:
            return False
        p = Path(path)
        if not p.exists():
            return False
        indicators = ["mods", "savegame1", "gameSettings.xml"]
        return any((p / i).exists() for i in indicators)

    @staticmethod
    def get_mods_path(base: str) -> str:
        return os.path.join(base, "mods")

    @staticmethod
    def get_settings_path(base: str) -> str:
        return os.path.join(base, "gameSettings.xml")

    @staticmethod
    def get_streaming_radio_path(base: str) -> str:
        return os.path.join(base, "music", "streamingInternetRadios.xml")

    @staticmethod
    def get_music_path(data_path: str) -> str:
        return os.path.join(data_path, "music")

    @staticmethod
    def get_log_path(base: str) -> str:
        return os.path.join(base, "log.txt")

    @staticmethod
    def get_save_path(base: str, slot: int) -> str:
        return os.path.join(base, f"savegame{slot}")
