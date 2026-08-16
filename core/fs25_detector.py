import os
import re
from pathlib import Path
from typing import Callable

from core.game_launcher import GameLauncher


class FS25Detector:
    """Detects Farming Simulator 25 user data path on Linux."""

    COMMON_PATHS = [
        "~/FarmingSimulator2025",
        "~/Documents/My Games/FarmingSimulator2025",
        "~/.local/share/FarmingSimulator2025",
        "~/snap/FarmingSimulator2025",
    ]

    # Steam installs FS25 through Proton, so the user data lives inside the
    # compatdata prefix rather than under $HOME.
    STEAM_ROOTS = [
        "~/.steam/steam",
        "~/.steam/root",
        "~/.local/share/Steam",
        "~/.var/app/com.valvesoftware.Steam/data/Steam",   # flatpak
        "~/snap/steam/common/.local/share/Steam",          # snap
        "/run/host/var/home/*/.local/share/Steam",         # distrobox, host $HOME
        "/run/host/var/home/*/.steam/steam",
    ]
    PREFIX_DATA_SUFFIX = "pfx/drive_c/users/steamuser/Documents/My Games/FarmingSimulator2025"
    # Documents is sometimes localised or redirected, so glob one level wide.
    PREFIX_DATA_GLOB = "pfx/drive_c/users/steamuser/*/My Games/FarmingSimulator2025"

    @classmethod
    def _expand_root(cls, root: str) -> list[Path]:
        """Expand ~ and any glob in a configured Steam root."""
        expanded = os.path.expanduser(root)
        if any(ch in expanded for ch in "*?["):
            return sorted(Path("/").glob(expanded.lstrip("/")))
        return [Path(expanded)]

    @classmethod
    def steam_libraries(cls) -> list[Path]:
        """Steam library roots, including extra drives from libraryfolders.vdf.

        Nothing here is machine specific: the roots are the standard Steam
        install locations, and any other library the user created is read out
        of Steam's own libraryfolders.vdf.
        """
        libraries: list[Path] = []
        seen: set[Path] = set()

        def remember(path: Path) -> None:
            if not path.is_dir():
                return
            try:
                key = path.resolve()
            except OSError:
                key = path
            if key not in seen:
                seen.add(key)
                libraries.append(path)

        for root in cls.STEAM_ROOTS:
            for base in cls._expand_root(root):
                steamapps = base / "steamapps"
                remember(steamapps)

                vdf = steamapps / "libraryfolders.vdf"
                if not vdf.is_file():
                    continue
                try:
                    text = vdf.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                # ponytail: regex over the vdf instead of a real parser; only
                # the "path" values matter. Use a vdf library if we need more.
                for match in re.finditer(r'"path"\s+"([^"]+)"', text):
                    remember(Path(match.group(1)) / "steamapps")

        return libraries

    @classmethod
    def candidate_paths(cls) -> list[Path]:
        """Every place FS25 user data could plausibly live, in priority order."""
        candidates = [Path(p).expanduser() for p in cls.COMMON_PATHS]
        for steamapps in cls.steam_libraries():
            compatdata = steamapps / "compatdata"
            if not compatdata.is_dir():
                continue
            try:
                prefixes = sorted(compatdata.iterdir())
            except OSError:
                continue
            for prefix in prefixes:
                candidates.append(prefix / cls.PREFIX_DATA_SUFFIX)
                candidates.extend(prefix.glob(cls.PREFIX_DATA_GLOB))

        seen: set[Path] = set()
        unique: list[Path] = []
        for path in candidates:
            if path not in seen:
                seen.add(path)
                unique.append(path)
        return unique

    @classmethod
    def search(cls, progress: Callable[[int, int, str], bool] | None = None) -> list[str]:
        """Scan every candidate path, returning the ones that hold FS25 data.

        `progress(done, total, path)` is called per candidate; return False from
        it to cancel the scan.
        """
        candidates = cls.candidate_paths()
        total = len(candidates)
        found: list[str] = []
        seen: set[Path] = set()
        for index, path in enumerate(candidates, start=1):
            if progress is not None and not progress(index, total, str(path)):
                break
            if not cls.validate_path(str(path)):
                continue
            # Proton prefixes symlink "My Documents" at "Documents", so the
            # same install can match more than once.
            try:
                key = path.resolve()
            except OSError:
                key = path
            if key not in seen:
                seen.add(key)
                found.append(str(path))
        return found

    @classmethod
    def find_user_data_path(cls) -> str | None:
        results = cls.search()
        return results[0] if results else None

    @classmethod
    def find_game_install(cls) -> str | None:
        """Locate the installed game folder via Steam's app manifest.

        The game can be installed while its user data does not exist yet:
        Proton only creates the prefix on the first launch.
        """
        for steamapps in cls.steam_libraries():
            manifest = steamapps / f"appmanifest_{GameLauncher.FS25_APP_ID}.acf"
            if not manifest.is_file():
                continue
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            match = re.search(r'"installdir"\s+"([^"]+)"', text)
            if not match:
                continue
            install = steamapps / "common" / match.group(1)
            if install.is_dir():
                return str(install)
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
