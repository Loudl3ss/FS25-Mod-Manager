import json
from dataclasses import asdict, dataclass
from pathlib import Path


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
        except Exception:
            pass
        return {}

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

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.config.update_from_dict(data)
        except Exception:
            pass

    def save(self):
        """Save configuration to disk."""
        try:
            payload = asdict(self.config)
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            # Keep bootstrap settings in sync so startup can resolve the manager home path.
            if self.bootstrap_config_path != self.config_path:
                self.bootstrap_config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.bootstrap_config_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=4)
        except Exception:
            pass

    @property
    def manager_home(self) -> str:
        return str(self.data_dir)

    def get_manager_home_for_root(self, root_path: str) -> str:
        return str(self.build_manager_home(root_path))
