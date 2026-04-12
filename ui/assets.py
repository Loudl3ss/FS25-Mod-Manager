"""Central icon registry for the application."""

import os

from PyQt6.QtGui import QIcon

class Icons:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    ICONS_PATH = os.path.abspath(os.path.join(BASE_DIR, "icons"))

    # Sidebar Navigation (icon file paths)
    NAV_MOD_MANAGER = "tractor.png"
    NAV_NEW_GAME    = "plus.png"
    NAV_SAVE_GAMES  = "save.png"
    NAV_FAVORITES   = "star_outline.png"
    NAV_MODS        = "package.png"
    NAV_MAPS        = "map.png"
    NAV_ABOUT       = "info.png"
    NAV_ONLINE_BROWSE = "globe.png"

    # Common UI Symbols (PNG file names)
    SAVE     = "save.png"
    MAP      = "map.png"
    PACKAGE  = "package.png"
    STAR     = "star_shine.png"
    STAR_OUTLINE = "star_outline.png"
    RESCAN   = "refresh.png"
    RESTORE  = "restore.png"
    FOLDER   = "folder.png"
    INFO     = "info.png"
    PLUS     = "plus.png"
    DELETE   = "delete.png"
    DOWNLOAD = "download.png"
    SETTINGS = "settings.png"
    APP_SETTINGS = "settings.png"
    SUCESFULL = "check.png"

    @classmethod
    def get_qicon(cls, icon_constant):
        full_path = os.path.abspath(os.path.join(cls.ICONS_PATH, icon_constant))

        if not os.path.exists(full_path):
            print(f"[Icons] Warning: Missing icon file at {full_path}")
            return QIcon()

        return QIcon(full_path)
