"""Central icon registry for the application."""

import os

from PyQt6.QtGui import QIcon

class Icons:
    ICONS_PATH = os.path.join(os.path.dirname(__file__), "icons")

    # Sidebar Navigation
    NAV_MOD_MANAGER = "agriculture_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_NEW_GAME = "add_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_SAVE_GAMES = "save_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_FAVORITES = "star_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_MODS = "package_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_MAPS = "map_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_ABOUT = "info_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    NAV_ONLINE_BROWSE = "globe_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"

    # Common UI Symbols
    SAVE = "save_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    MAP = "map_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    PACKAGE = "package_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    STAR = "star_shine_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    STAR_OUTLINE = "star_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    RESCAN = "refresh_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    RESTORE = "done_outline_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    FOLDER = "folder_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    INFO = "info_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    PLUS = "add_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    DELETE = "delete_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    DOWNLOAD = "download_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    APP_SETTINGS = "settings_applications_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    SUCESFULL = "check_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    COUNTER_1 = "counter_1_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    COUNTER_2 = "counter_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
    COUNTER_3 = "counter_3_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"

    @classmethod
    def get_qicon(cls, icon_constant):
        full_path = os.path.join(cls.ICONS_PATH, icon_constant)

        if not os.path.exists(full_path):
            print(f"[Icons] Warning: Missing icon file at {full_path}")
            return QIcon()

        return QIcon(full_path)
