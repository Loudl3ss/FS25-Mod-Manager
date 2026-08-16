import json
from dataclasses import asdict, dataclass
from pathlib import Path

from core.logging_utils import get_logger


logger = get_logger("app_config")


@dataclass
class AppConfig:
    # Folder paths for game and save files
    mods_folder: str = ""
    savedgames_folder: str = ""
    game_install_path: str = ""
    backup_folder: str = ""
    manager_cache_root: str = ""

    def update_from_dict(self, data: dict):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)


class AppConfigManager:
    """Manages the application-level settings stored in JSON."""

    def __init__(self, data_dir: str):
        self.bootstrap_dir = Path(data_dir)
        self.bootstrap_config_path = self.bootstrap_dir / "app_settings.json"
        cache_root = self._resolve_cache_root_from_bootstrap()
        self.data_dir = self.build_manager_home(cache_root)
        self.config_path = self.data_dir / "app_settings.json"
        self.config = AppConfig()
        self.load()

    @staticmethod
    def build_manager_home(root_path: str | Path) -> Path:
        return Path(root_path).expanduser() / "FS25_Mod_manager"

    def _read_json(self, path: Path) -> dict:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            logger.warning("Failed to read JSON from %s: %s", path, exc)
        return {}

    def _write_json(self, path: Path, payload: dict) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            return True
        except (OSError, TypeError, ValueError) as exc:
            logger.warning("Failed to write JSON to %s: %s", path, exc)
            return False

    def _resolve_cache_root_from_bootstrap(self) -> Path:
        data = self._read_json(self.bootstrap_config_path)
        cache_root = str(data.get("manager_cache_root", "")).strip()
        if cache_root:
            return Path(cache_root).expanduser()

        game_install_path = str(data.get("game_install_path", "")).strip()
        if game_install_path:
            return Path(game_install_path).expanduser()

        return self.bootstrap_dir

    def load(self):
        """Load configuration from disk."""
        if not self.config_path.exists():
            legacy_data = self._read_json(self.bootstrap_config_path)
            if legacy_data:
                self.config.update_from_dict(legacy_data)
            self.save()  # create defaults
            return

        data = self._read_json(self.config_path)
        if data:
            self.config.update_from_dict(data)

    def save(self):
        """Save configuration to disk."""
        payload = asdict(self.config)
        if not self._write_json(self.config_path, payload):
            return

        # Keep bootstrap settings in sync so startup can resolve the manager home path.
        if self.bootstrap_config_path != self.config_path:
            self._write_json(self.bootstrap_config_path, payload)

    def autofill_defaults(self, data_path: str, game_install_path: str = "") -> list[str]:
        """Fill in any path the user has not set, from the detected install.

        Only empty fields are touched, so a path the user chose by hand always
        wins. Returns the names of the fields that were filled.
        """
        base = Path(data_path).expanduser()
        defaults = {
            "mods_folder": str(base / "mods"),
            "savedgames_folder": str(base),
            "manager_cache_root": str(base),
            "backup_folder": str(self.data_dir / "backups"),
        }
        if game_install_path:
            defaults["game_install_path"] = game_install_path

        filled = [
            key for key, value in defaults.items()
            if not str(getattr(self.config, key, "")).strip() and value
        ]
        for key in filled:
            setattr(self.config, key, defaults[key])

        if filled:
            self.save()
        return filled

    @property
    def manager_home(self) -> str:
        return str(self.data_dir)

    def get_manager_home_for_root(self, root_path: str) -> str:
        return str(self.build_manager_home(root_path))
