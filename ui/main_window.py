
"""Main application window with sidebar navigation."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
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
from core.mod_manager import ModManager
from core.save_manager import SaveManager

from ui.about_page import AboutPage
from ui.app_settings_page import AppSettingsPage
from ui.assets import Icons
from ui.library_pages import LibraryFavoritesPage, LibraryModsPage, LibraryMapsPage
from ui.mods_page import ModsPage
from ui.new_game_page import NewGameView
from ui.online_mods_page import OnlineModsPage
from ui.saves_page import SavesPage
from ui.widgets import SidebarNavButton



class MainWindow(QMainWindow):
    def __init__(self, data_path: str):
        super().__init__()
        self._data_path = data_path

        # ── Backend managers ─────────────────────────────────────────────────
        mods_path = FS25Detector.get_mods_path(data_path)
        self._mods_path = mods_path
        settings_path = FS25Detector.get_settings_path(data_path)

        self._mod_manager = ModManager(mods_path)
        self._save_manager = SaveManager(data_path)
        self._favorites_manager = FavoritesManager(
            f"{data_path}/fs25manager_favorites.json"
        )
        self._app_config_manager = AppConfigManager(data_path)
        self._opening_new_game = False

        self._build_ui()

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

        # --- Workplace Section ---
        workplace_label = QLabel("WORKPLACE")
        workplace_label.setObjectName("SidebarSection")
        sb_lay.addWidget(workplace_label)
        workplace_widget = QWidget()
        workplace_layout = QVBoxLayout(workplace_widget)
        workplace_layout.setContentsMargins(12, 0, 8, 0)
        workplace_layout.setSpacing(0)
        nav_icon_size = QSize(24, 24)
        self._nav_buttons: list[QPushButton] = []
        self.btn_mod_manager = SidebarNavButton("Mod Manager", "[ M ]")
        self.btn_mod_manager.setIcon(Icons.get_qicon(Icons.NAV_MOD_MANAGER))
        self.btn_mod_manager.setIconSize(nav_icon_size)
        self.btn_mod_manager.clicked.connect(lambda: self._switch_page(0))
        workplace_layout.addWidget(self.btn_mod_manager)
        self._nav_buttons.append(self.btn_mod_manager)

        self.btn_new_game = SidebarNavButton("New Game", "[ N ]")
        self.btn_new_game.setIcon(Icons.get_qicon(Icons.NAV_NEW_GAME))
        self.btn_new_game.setIconSize(nav_icon_size)
        self.btn_new_game.clicked.connect(lambda: self._switch_page(1))
        workplace_layout.addWidget(self.btn_new_game)
        self._nav_buttons.append(self.btn_new_game)

        self.btn_save_games = SidebarNavButton("Save Games", "[ S ]")
        self.btn_save_games.setIcon(Icons.get_qicon(Icons.NAV_SAVE_GAMES))
        self.btn_save_games.setIconSize(nav_icon_size)
        self.btn_save_games.clicked.connect(lambda: self._switch_page(2))
        workplace_layout.addWidget(self.btn_save_games)
        self._nav_buttons.append(self.btn_save_games)
        sb_lay.addWidget(workplace_widget)

        # --- Library Section ---
        library_label = QLabel("LIBRARY")
        library_label.setObjectName("SidebarSection")
        sb_lay.addWidget(library_label)
        library_widget = QWidget()
        library_layout = QVBoxLayout(library_widget)
        library_layout.setContentsMargins(12, 0, 8, 0)
        library_layout.setSpacing(0)
        self.btn_favorites = SidebarNavButton("Favourites", "[ F ]")
        self.btn_favorites.setIcon(Icons.get_qicon(Icons.NAV_FAVORITES))
        self.btn_favorites.setIconSize(nav_icon_size)
        self.btn_favorites.clicked.connect(lambda: self._switch_page(3))
        library_layout.addWidget(self.btn_favorites)
        self._nav_buttons.append(self.btn_favorites)
        self.btn_mods = SidebarNavButton("All Mods", "[ A ]")
        self.btn_mods.setIcon(Icons.get_qicon(Icons.NAV_MODS))
        self.btn_mods.setIconSize(nav_icon_size)
        self.btn_mods.clicked.connect(lambda: self._switch_page(4))
        library_layout.addWidget(self.btn_mods)
        self._nav_buttons.append(self.btn_mods)
        self.btn_maps = SidebarNavButton("Maps", "[ P ]")
        self.btn_maps.setIcon(Icons.get_qicon(Icons.NAV_MAPS))
        self.btn_maps.setIconSize(nav_icon_size)
        self.btn_maps.clicked.connect(lambda: self._switch_page(5))
        library_layout.addWidget(self.btn_maps)
        self._nav_buttons.append(self.btn_maps)
        sb_lay.addWidget(library_widget)

        # --- FS25 Section ---
        online_label = QLabel("Online Mods")
        online_label.setObjectName("SidebarSection")
        sb_lay.addWidget(online_label)
        online_widget = QWidget()
        online_layout = QVBoxLayout(online_widget)
        online_layout.setContentsMargins(12, 0, 8, 0)
        online_layout.setSpacing(0)
        self.btn_online = SidebarNavButton("FS25 Official", "[ G ]")
        self.btn_online.setIcon(Icons.get_qicon(Icons.NAV_ONLINE_BROWSE))
        self.btn_online.setIconSize(nav_icon_size)
        self.btn_online.clicked.connect(lambda: self._switch_page(6))
        online_layout.addWidget(self.btn_online)
        self._nav_buttons.append(self.btn_online)

        self.btn_kingmods = SidebarNavButton("KINGMODS", "[ K ]")
        self.btn_kingmods.setIcon(Icons.get_qicon(Icons.NAV_ONLINE_BROWSE))
        self.btn_kingmods.setIconSize(nav_icon_size)
        self.btn_kingmods.clicked.connect(lambda: self._switch_page(7))
        online_layout.addWidget(self.btn_kingmods)
        self._nav_buttons.append(self.btn_kingmods)

        self.btn_fs25net = SidebarNavButton("FS25.NET", "[ N ]")
        self.btn_fs25net.setIcon(Icons.get_qicon(Icons.NAV_ONLINE_BROWSE))
        self.btn_fs25net.setIconSize(nav_icon_size)
        self.btn_fs25net.clicked.connect(lambda: self._switch_page(8))
        online_layout.addWidget(self.btn_fs25net)
        self._nav_buttons.append(self.btn_fs25net)
        sb_lay.addWidget(online_widget)

        sb_lay.addStretch()

        # 3. About (Bottom Utility)
        # App Settings (just above About)
        self.btn_app_settings = SidebarNavButton("App Settings", "[ C ]")
        self.btn_app_settings.setIcon(Icons.get_qicon(Icons.APP_SETTINGS))
        self.btn_app_settings.setIconSize(nav_icon_size)
        self.btn_app_settings.clicked.connect(lambda: self._switch_page(9))
        sb_lay.addWidget(self.btn_app_settings)
        self._nav_buttons.append(self.btn_app_settings)

        # About (Bottom Utility)
        self.btn_about = SidebarNavButton("About", "[ I ]")
        self.btn_about.setIcon(Icons.get_qicon(Icons.NAV_ABOUT))
        self.btn_about.setIconSize(nav_icon_size)
        self.btn_about.clicked.connect(lambda: self._switch_page(10))
        sb_lay.addWidget(self.btn_about)
        self._nav_buttons.append(self.btn_about)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #1e293b;")
        sb_lay.addWidget(divider)

        # Bottom "Open Folder" button
        btn_folder = QPushButton("📂  Open Game Folder")
        btn_folder.setObjectName("ToolBtn")
        btn_folder.setContentsMargins(8, 4, 8, 4)
        btn_folder.clicked.connect(self._open_folder)
        sb_lay.addWidget(btn_folder)

        sb_lay.addSpacing(12)

        root.addWidget(sidebar)

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
        self._app_settings_page = AppSettingsPage(app_config_manager=self._app_config_manager)
        self._app_settings_page.rescan_requested.connect(self._mods_page._load_mods)
        self._app_settings_page.rescan_requested.connect(self._refresh_library_badges)
        self._about_page = AboutPage()

        self._stack.addWidget(self._mods_page)         # Index 0 (Mod Manager)
        self._stack.addWidget(self._new_game_page)     # Index 1 (New Game)
        self._stack.addWidget(self._saves_page)        # Index 2 (Save Games)
        self._stack.addWidget(self._favorites_page)    # Index 3 (Favorites)
        self._stack.addWidget(self._all_mods_page)     # Index 4 (All Mods)
        self._stack.addWidget(self._maps_page)         # Index 5 (Maps)
        self._stack.addWidget(self._online_mods_page)  # Index 6 (Online Mods - FS25 Official)
        self._stack.addWidget(self._kingmods_page)     # Index 7 (KINGMODS)
        self._stack.addWidget(self._fs25net_page)      # Index 8 (FS25.NET)
        self._stack.addWidget(self._app_settings_page) # Index 9 (App Settings)
        self._stack.addWidget(self._about_page)        # Index 10 (About)

        root.addWidget(self._stack, stretch=1)

        # Select first nav item
        self._switch_page(0)
        self._refresh_library_badges()

    def _is_map_mod(self, mod) -> bool:
        return "map" in (getattr(mod, "category", "") or "").lower()

    def _refresh_library_badges(self):
        mods = list(getattr(self._mods_page, "_mods", []))
        if not mods:
            try:
                mods = self._mod_manager.get_mods()
            except Exception:
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
        if index == 1: # New Game
            self._new_game_page.populate_data()

        if index in (3, 4, 5):
            self._refresh_library_badges()
            
        for i, btn in enumerate(self._nav_buttons):
            active = i == index
            btn.setProperty("active", "true" if active else "false")
            btn.setChecked(active)
            style = btn.style()
            if style is not None:
                style.unpolish(btn)
                style.polish(btn)

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
        self._switch_page(1)
        self._new_game_page.open_map_step()
        self._opening_new_game = False
