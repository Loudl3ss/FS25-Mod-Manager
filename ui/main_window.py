
"""Main application window with sidebar navigation."""
from __future__ import annotations

import sqlite3

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from core.favorites_manager import FavoritesManager
from core.app_config import AppConfigManager
from core.fs25_detector import FS25Detector
from core.fs25net_scraper import FS25NetScraper
from core.kingmods_scraper import KingModsScraper
from core.game_launcher import GameLauncher
from core.log_analyzer import LogAnalyzer
from core.mod_manager import ModManager
from core.radio_manager import RadioManager
from core.save_manager import SaveManager

from ui.about_page import AboutPage
from ui.app_settings_page import AppSettingsPage
from ui.assets import Icons
from ui.library_pages import LibraryFavoritesPage, LibraryModsPage, LibraryMapsPage
from ui.log_viewer_page import LogViewerPage
from ui.mods_page import ModsPage
from ui.new_game_page import NewGameView
from ui.online_mods_page import OnlineModsPage
from ui.radio_settings_page import RadioSettingsPage
from ui.saves_page import SavesPage
from ui.style_helpers import refresh_widget_style, set_bool_property
from ui.widgets import SidebarNavButton



class MainWindow(QMainWindow):
    PAGE_MOD_MANAGER = 0
    PAGE_NEW_GAME = 1
    PAGE_SAVE_GAMES = 2
    PAGE_RADIO_SETTINGS = 3
    PAGE_FAVORITES = 4
    PAGE_ALL_MODS = 5
    PAGE_MAPS = 6
    PAGE_ONLINE_OFFICIAL = 7
    PAGE_KINGMODS = 8
    PAGE_FS25NET = 9
    PAGE_LOG_ANALYZER = 10
    PAGE_APP_SETTINGS = 11
    PAGE_ABOUT = 12

    LIBRARY_PAGE_IDS = (PAGE_FAVORITES, PAGE_ALL_MODS, PAGE_MAPS)

    def __init__(self, data_path: str):
        super().__init__()
        self._data_path = data_path

        # ── Backend managers ─────────────────────────────────────────────────
        mods_path = FS25Detector.get_mods_path(data_path)
        self._mods_path = mods_path

        self._app_config_manager = AppConfigManager(data_path)
        self._manager_home = self._app_config_manager.manager_home
        self._mod_manager = ModManager(mods_path, app_cache_root=self._manager_home)
        self._radio_manager = RadioManager(
            FS25Detector.get_streaming_radio_path(data_path)
        )
        self._log_analyzer = LogAnalyzer(data_path)
        self._save_manager = SaveManager(
            data_path,
            backup_dir=self._app_config_manager.config.backup_folder,
            default_backup_base=self._manager_home,
        )
        self._favorites_manager = FavoritesManager(
            f"{self._manager_home}/fs25manager_favorites.json"
        )
        self._opening_new_game = False

        self._build_ui()

    def _add_sidebar_nav_button(
        self,
        layout: QVBoxLayout,
        text: str,
        shortcut: str,
        icon_name: str,
        page_id: int,
        icon_size: QSize,
    ) -> SidebarNavButton:
        button = SidebarNavButton(text, shortcut)
        button.setIcon(Icons.get_qicon(icon_name))
        button.setIconSize(icon_size)
        button.clicked.connect(lambda: self._switch_page(page_id))
        layout.addWidget(button)
        self._nav_buttons.append(button)
        return button

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("FS25 Manager")
        self.setMinimumSize(1000, 680)
        self.resize(1180, 740)

        # Root horizontal layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        nav_icon_size = QSize(24, 24)
        root.addWidget(self._build_sidebar(nav_icon_size))
        self._build_pages()
        root.addWidget(self._stack, stretch=1)

        # Select first nav item
        self._switch_page(self.PAGE_MOD_MANAGER)
        self._refresh_library_badges()

    def _build_sidebar(self, nav_icon_size: QSize) -> QScrollArea:
        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(16, 0, 8, 0)
        sb_lay.setSpacing(0)

        # Logo block
        logo = QLabel(
            '<span style="font-family: Impact, \'Arial Black\', \'Segoe UI\', sans-serif; '
            'font-size: 36px; font-weight: 900; color: #e5e7eb; letter-spacing: 0.5px;">FS</span>'
            '<span style="font-family: Impact, \'Arial Black\', \'Segoe UI\', sans-serif; '
            'font-size: 28px; font-weight: 900; color: #ffffff; background: #84cc16; '
            'border: 1px solid #65a30d; border-radius: 8px; padding: 0 8px; margin-left: 6px;">25</span>'
        )
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setObjectName("SidebarLogo")
        sb_lay.addWidget(logo)

        sub = QLabel("MANAGER")
        sub.setObjectName("SidebarSubtitle")
        sb_lay.addWidget(sub)

        self._nav_buttons: list[SidebarNavButton] = []

        self._build_workplace_section(sb_lay, nav_icon_size)
        self._build_library_section(sb_lay, nav_icon_size)
        self._build_online_section(sb_lay, nav_icon_size)

        sb_lay.addStretch()
        self._build_tools_section(sb_lay, nav_icon_size)

        sb_lay.addStretch(1)

        self.btn_launch_game = QPushButton("LAUNCH GAME")
        self.btn_launch_game.setObjectName("LaunchBtn")
        self.btn_launch_game.clicked.connect(GameLauncher.launch_steam_game)
        sb_lay.addWidget(self.btn_launch_game)

        self._build_utility_section(sb_lay, nav_icon_size)

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("SidebarScroll")
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setWidget(sidebar)
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Reserve a slim lane so overlay scrollbars do not cover nav badges.
        sidebar_scroll.setViewportMargins(0, 0, 2, 0)
        return sidebar_scroll

    def _build_workplace_section(self, sb_lay: QVBoxLayout, nav_icon_size: QSize) -> None:
        workplace_label = QLabel("WORKPLACE")
        workplace_label.setObjectName("SidebarSection")
        sb_lay.addWidget(workplace_label)
        workplace_widget = QWidget()
        workplace_layout = QVBoxLayout(workplace_widget)
        workplace_layout.setContentsMargins(12, 0, 8, 0)
        workplace_layout.setSpacing(0)
        self.btn_mod_manager = self._add_sidebar_nav_button(
            workplace_layout,
            "Mod Manager",
            "[ M ]",
            Icons.NAV_MOD_MANAGER,
            self.PAGE_MOD_MANAGER,
            nav_icon_size,
        )
        self.btn_new_game = self._add_sidebar_nav_button(
            workplace_layout,
            "New Game",
            "[ N ]",
            Icons.NAV_NEW_GAME,
            self.PAGE_NEW_GAME,
            nav_icon_size,
        )
        self.btn_save_games = self._add_sidebar_nav_button(
            workplace_layout,
            "Save Games",
            "[ S ]",
            Icons.NAV_SAVE_GAMES,
            self.PAGE_SAVE_GAMES,
            nav_icon_size,
        )
        self.btn_radio = self._add_sidebar_nav_button(
            workplace_layout,
            "Radio Settings",
            "[ R ]",
            Icons.NAV_ONLINE_BROWSE,
            self.PAGE_RADIO_SETTINGS,
            nav_icon_size,
        )
        sb_lay.addWidget(workplace_widget)

    def _build_library_section(self, sb_lay: QVBoxLayout, nav_icon_size: QSize) -> None:
        library_label = QLabel("LIBRARY")
        library_label.setObjectName("SidebarSection")
        sb_lay.addWidget(library_label)
        library_widget = QWidget()
        library_layout = QVBoxLayout(library_widget)
        library_layout.setContentsMargins(12, 0, 8, 0)
        library_layout.setSpacing(0)
        self.btn_favorites = self._add_sidebar_nav_button(
            library_layout,
            "Favourites",
            "[ F ]",
            Icons.NAV_FAVORITES,
            self.PAGE_FAVORITES,
            nav_icon_size,
        )
        self.btn_mods = self._add_sidebar_nav_button(
            library_layout,
            "All Mods",
            "[ A ]",
            Icons.NAV_MODS,
            self.PAGE_ALL_MODS,
            nav_icon_size,
        )
        self.btn_maps = self._add_sidebar_nav_button(
            library_layout,
            "Maps",
            "[ P ]",
            Icons.NAV_MAPS,
            self.PAGE_MAPS,
            nav_icon_size,
        )
        sb_lay.addWidget(library_widget)

    def _build_online_section(self, sb_lay: QVBoxLayout, nav_icon_size: QSize) -> None:
        online_label = QLabel("Online Mods")
        online_label.setObjectName("SidebarSection")
        sb_lay.addWidget(online_label)
        online_widget = QWidget()
        online_layout = QVBoxLayout(online_widget)
        online_layout.setContentsMargins(12, 0, 8, 0)
        online_layout.setSpacing(0)
        self.btn_online = self._add_sidebar_nav_button(
            online_layout,
            "FS25 Official",
            "[ G ]",
            Icons.NAV_ONLINE_BROWSE,
            self.PAGE_ONLINE_OFFICIAL,
            nav_icon_size,
        )
        self.btn_kingmods = self._add_sidebar_nav_button(
            online_layout,
            "KINGMODS",
            "[ K ]",
            Icons.NAV_ONLINE_BROWSE,
            self.PAGE_KINGMODS,
            nav_icon_size,
        )
        self.btn_fs25net = self._add_sidebar_nav_button(
            online_layout,
            "FS25.NET",
            "[ N ]",
            Icons.NAV_ONLINE_BROWSE,
            self.PAGE_FS25NET,
            nav_icon_size,
        )
        sb_lay.addWidget(online_widget)

    def _build_tools_section(self, sb_lay: QVBoxLayout, nav_icon_size: QSize) -> None:
        tools_label = QLabel("TOOLS")
        tools_label.setObjectName("SidebarSection")
        sb_lay.addWidget(tools_label)
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(12, 0, 8, 0)
        tools_layout.setSpacing(0)
        self.btn_log = self._add_sidebar_nav_button(
            tools_layout,
            "Log Analyzer",
            "[ ! ]",
            Icons.NAV_LOG_SCANNER,
            self.PAGE_LOG_ANALYZER,
            nav_icon_size,
        )
        sb_lay.addWidget(tools_widget)

    def _build_utility_section(self, sb_lay: QVBoxLayout, nav_icon_size: QSize) -> None:
        self.btn_app_settings = self._add_sidebar_nav_button(
            sb_lay,
            "App Settings",
            "[ C ]",
            Icons.APP_SETTINGS,
            self.PAGE_APP_SETTINGS,
            nav_icon_size,
        )

        self.btn_about = self._add_sidebar_nav_button(
            sb_lay,
            "About",
            "[ I ]",
            Icons.NAV_ABOUT,
            self.PAGE_ABOUT,
            nav_icon_size,
        )

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #1e293b;")
        sb_lay.addWidget(divider)

        btn_folder = QPushButton("📂  Open Game Folder")
        btn_folder.setObjectName("ToolBtn")
        btn_folder.setContentsMargins(8, 4, 8, 4)
        btn_folder.clicked.connect(self._open_folder)
        sb_lay.addWidget(btn_folder)

        sb_lay.addSpacing(12)

    def _build_pages(self) -> None:
        # ── Stacked content ──────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("ContentArea")

        self._new_game_page = NewGameView(self._mod_manager, self._save_manager, self._favorites_manager)

        self._favorites_page = LibraryFavoritesPage(
            self._mod_manager,
            self._favorites_manager,
            self._app_config_manager,
        )
        self._all_mods_page = LibraryModsPage(
            self._mod_manager,
            self._favorites_manager,
            self._app_config_manager,
        )
        self._maps_page = LibraryMapsPage(
            self._mod_manager,
            self._favorites_manager,
            self._app_config_manager,
        )
        self._online_mods_page = OnlineModsPage(self._mods_path)
        self._kingmods_page = OnlineModsPage(
            self._mods_path,
            scraper_factory=KingModsScraper,
            page_title="KINGMODS",
            page_subtitle="Browse FS25 community mods on KingMods",
            default_filter="new-mods",
            default_filter_label="Latest",
        )
        self._fs25net_page = OnlineModsPage(
            self._mods_path,
            scraper_factory=FS25NetScraper,
            page_title="FS25.NET",
            page_subtitle="Browse FS25 community mods on FS25.NET",
            default_filter="latest",
            default_filter_label="Latest",
        )

        self._mods_page = ModsPage(self._mod_manager, self._favorites_manager, show_new_game_button=True)
        self._mods_page.favorite_changed.connect(self._on_mod_favorite_changed)
        self._mods_page.mods_loaded.connect(self._refresh_library_badges)
        self._mods_page.request_new_game.connect(self._open_new_game_wizard)
        self._saves_page = SavesPage(self._save_manager)
        self._radio_settings_page = RadioSettingsPage(
            self._radio_manager,
            FS25Detector.get_music_path(data_path=self._data_path),
        )
        self._log_viewer_page = LogViewerPage(self._log_analyzer)
        self._app_settings_page = AppSettingsPage(app_config_manager=self._app_config_manager)
        self._app_settings_page.rescan_requested.connect(self._mods_page.reload_mods)
        self._app_settings_page.rescan_requested.connect(self._refresh_library_badges)
        self._app_settings_page.backup_folder_changed.connect(self._on_backup_folder_changed)
        self._app_settings_page.manager_cache_root_changed.connect(self._on_manager_cache_root_changed)
        self._about_page = AboutPage()

        self._stack.addWidget(self._mods_page)         # PAGE_MOD_MANAGER
        self._stack.addWidget(self._new_game_page)     # PAGE_NEW_GAME
        self._stack.addWidget(self._saves_page)        # PAGE_SAVE_GAMES
        self._stack.addWidget(self._radio_settings_page) # PAGE_RADIO_SETTINGS
        self._stack.addWidget(self._favorites_page)    # PAGE_FAVORITES
        self._stack.addWidget(self._all_mods_page)     # PAGE_ALL_MODS
        self._stack.addWidget(self._maps_page)         # PAGE_MAPS
        self._stack.addWidget(self._online_mods_page)  # PAGE_ONLINE_OFFICIAL
        self._stack.addWidget(self._kingmods_page)     # PAGE_KINGMODS
        self._stack.addWidget(self._fs25net_page)      # PAGE_FS25NET
        self._stack.addWidget(self._log_viewer_page)   # PAGE_LOG_ANALYZER
        self._stack.addWidget(self._app_settings_page) # PAGE_APP_SETTINGS
        self._stack.addWidget(self._about_page)        # PAGE_ABOUT

    def _is_map_mod(self, mod) -> bool:
        return "map" in (getattr(mod, "category", "") or "").lower()

    def _refresh_library_badges(self):
        mods = self._mods_page.get_loaded_mods()
        if not mods:
            try:
                mods = self._mod_manager.get_mods()
            except (OSError, sqlite3.Error):
                mods = []

        map_count = sum(1 for m in mods if self._is_map_mod(m))
        all_mods_count = max(0, len(mods) - map_count)

        favorites = self._favorites_manager.favorites
        fav_count = sum(
            1
            for m in mods
            if (m.id in favorites) or (getattr(m, "filename", "") in favorites)
        )

        self.btn_favorites.set_badge_count(fav_count)
        self.btn_mods.set_badge_count(all_mods_count)
        self.btn_maps.set_badge_count(map_count)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _switch_page(self, index: int):
        self._stack.setCurrentIndex(index)
        
        # Trigger data population for specific pages
        if index == self.PAGE_NEW_GAME:
            self._new_game_page.populate_data()

        if index in self.LIBRARY_PAGE_IDS:
            self._refresh_library_badges()
            
        for i, btn in enumerate(self._nav_buttons):
            active = i == index
            set_bool_property(btn, "active", active)
            btn.setChecked(active)

    def _open_folder(self):
        import subprocess
        subprocess.Popen(["xdg-open", self._data_path])

    def _on_mod_favorite_changed(self, mod_id: str, is_fav: bool):
        self._refresh_library_badges()

    def _open_new_game_wizard(self):
        """Open New Game page and focus the map selection step."""
        if self._opening_new_game:
            return
        self._opening_new_game = True
        self._switch_page(self.PAGE_NEW_GAME)
        self._new_game_page.open_map_step()
        self._opening_new_game = False

    def _on_backup_folder_changed(self, backup_folder: str):
        self._save_manager.set_backup_dir(backup_folder)
        self._saves_page._load_saves()

    def _on_manager_cache_root_changed(self, root_path: str):
        manager_home = self._app_config_manager.get_manager_home_for_root(root_path)
        self._save_manager.set_default_backup_base(manager_home)
        if not self._app_config_manager.config.backup_folder:
            self._save_manager.set_backup_dir("")
            self._saves_page._load_saves()

        QMessageBox.information(
            self,
            "Restart Required",
            "Cache location was updated. Restart the app to move all manager data usage to the new FS25_Mod_manager folder.",
        )
