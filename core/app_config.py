import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    # Mod Manager filtering variables
    show_favorites_in_all_mods: bool = False
    include_maps_in_all_mods: bool = False
    strict_map_filtering: bool = True

    def update_from_dict(self, data: dict):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)


class AppConfigManager:
    """Manages the application-level settings stored in JSON."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.config_path = self.data_dir / "app_settings.json"
        self.config = AppConfig()
        self.load()

    def load(self):
        """Load configuration from disk."""
        if not self.config_path.exists():
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
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, indent=4)
        except Exception:
            pass
