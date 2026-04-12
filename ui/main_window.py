
"""Main application window with sidebar navigation."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
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
from core.mod_manager import ModManager
from core.save_manager import SaveManager

from ui.about_page import AboutPage
from ui.app_settings_page import AppSettingsPage
from ui.assets import Icons
from ui.library_pages import LibraryFavoritesPage, LibraryModsPage, LibraryMapsPage
from ui.mods_page import ModsPage
from ui.new_game_page import NewGameView
from ui.saves_page import SavesPage



class MainWindow(QMainWindow):
    def __init__(self, data_path: str):
        super().__init__()
        self._data_path = data_path

        # ── Backend managers ─────────────────────────────────────────────────
        mods_path = FS25Detector.get_mods_path(data_path)
        settings_path = FS25Detector.get_settings_path(data_path)

        self._mod_manager = ModManager(mods_path)
        self._save_manager = SaveManager(data_path)
        self._favorites_manager = FavoritesManager(
            f"{data_path}/fs25manager_favorites.json"
        )
        self._app_config_manager = AppConfigManager(data_path)

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
        sb_lay.setContentsMargins(16, 0, 0, 0)
        sb_lay.setSpacing(0)

        # Logo block
        logo = QLabel("FS25")
        logo.setObjectName("SidebarLogo")
        logo.setFont(QFont("", 20, QFont.Weight.Bold))
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
        workplace_layout.setContentsMargins(12, 0, 0, 0)
        workplace_layout.setSpacing(0)
        self._nav_buttons: list[QPushButton] = []
        self.btn_mod_manager = QPushButton("Mod Manager")
        self.btn_mod_manager.setObjectName("NavBtn")
        self.btn_mod_manager.setCheckable(True)
        self.btn_mod_manager.setIcon(Icons.get_qicon(Icons.NAV_MOD_MANAGER))
        self.btn_mod_manager.setIconSize(QSize(20, 20))
        self.btn_mod_manager.clicked.connect(lambda: self._switch_page(0))
        workplace_layout.addWidget(self.btn_mod_manager)
        self._nav_buttons.append(self.btn_mod_manager)

        self.btn_new_game = QPushButton("New Game")
        self.btn_new_game.setObjectName("NavBtn")
        self.btn_new_game.setCheckable(True)
        self.btn_new_game.setIcon(Icons.get_qicon(Icons.NAV_NEW_GAME))
        self.btn_new_game.setIconSize(QSize(20, 20))
        self.btn_new_game.clicked.connect(lambda: self._switch_page(1))
        workplace_layout.addWidget(self.btn_new_game)
        self._nav_buttons.append(self.btn_new_game)

        self.btn_save_games = QPushButton("Save Games")
        self.btn_save_games.setObjectName("NavBtn")
        self.btn_save_games.setCheckable(True)
        self.btn_save_games.setIcon(Icons.get_qicon(Icons.NAV_SAVE_GAMES))
        self.btn_save_games.setIconSize(QSize(20, 20))
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
        library_layout.setContentsMargins(12, 0, 0, 0)
        library_layout.setSpacing(0)
        self.btn_favorites = QPushButton("Favourites")
        self.btn_favorites.setObjectName("NavBtn")
        self.btn_favorites.setCheckable(True)
        self.btn_favorites.setIcon(Icons.get_qicon(Icons.NAV_FAVORITES))
        self.btn_favorites.setIconSize(QSize(20, 20))
        self.btn_favorites.clicked.connect(lambda: self._switch_page(3))
        library_layout.addWidget(self.btn_favorites)
        self._nav_buttons.append(self.btn_favorites)
        self.btn_mods = QPushButton("All Mods")
        self.btn_mods.setObjectName("NavBtn")
        self.btn_mods.setCheckable(True)
        self.btn_mods.setIcon(Icons.get_qicon(Icons.NAV_MODS))
        self.btn_mods.setIconSize(QSize(20, 20))
        self.btn_mods.clicked.connect(lambda: self._switch_page(4))
        library_layout.addWidget(self.btn_mods)
        self._nav_buttons.append(self.btn_mods)
        self.btn_maps = QPushButton("Maps")
        self.btn_maps.setObjectName("NavBtn")
        self.btn_maps.setCheckable(True)
        self.btn_maps.setIcon(Icons.get_qicon(Icons.NAV_MAPS))
        self.btn_maps.setIconSize(QSize(20, 20))
        self.btn_maps.clicked.connect(lambda: self._switch_page(5))
        library_layout.addWidget(self.btn_maps)
        self._nav_buttons.append(self.btn_maps)
        sb_lay.addWidget(library_widget)

        # --- Online Mods Section ---
        online_label = QLabel("ONLINE MODS")
        online_label.setObjectName("SidebarSection")
        sb_lay.addWidget(online_label)
        online_widget = QWidget()
        online_layout = QVBoxLayout(online_widget)
        online_layout.setContentsMargins(12, 0, 0, 0)
        online_layout.setSpacing(0)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setObjectName("NavBtn")
        self.btn_browse.setCheckable(True)
        self.btn_browse.setIcon(Icons.get_qicon(Icons.NAV_ONLINE_BROWSE))
        self.btn_browse.setIconSize(QSize(20, 20))
        online_layout.addWidget(self.btn_browse)
        self._nav_buttons.append(self.btn_browse)
        sb_lay.addWidget(online_widget)

        sb_lay.addStretch()

        # 3. About (Bottom Utility)
        # App Settings (just above About)
        self.btn_app_settings = QPushButton("App Settings")
        self.btn_app_settings.setObjectName("NavBtn")
        self.btn_app_settings.setCheckable(True)
        self.btn_app_settings.setIcon(Icons.get_qicon(Icons.APP_SETTINGS))
        self.btn_app_settings.setIconSize(QSize(20, 20))
        self.btn_app_settings.clicked.connect(lambda: self._switch_page(6))
        sb_lay.addWidget(self.btn_app_settings)
        self._nav_buttons.append(self.btn_app_settings)

        # About (Bottom Utility)
        self.btn_about = QPushButton("About")
        self.btn_about.setObjectName("NavBtn")
        self.btn_about.setCheckable(True)
        self.btn_about.setIcon(Icons.get_qicon(Icons.NAV_ABOUT))
        self.btn_about.setIconSize(QSize(20, 20))
        self.btn_about.clicked.connect(lambda: self._switch_page(7))
        sb_lay.addWidget(self.btn_about)
        self._nav_buttons.append(self.btn_about)

        # Path info at bottom of sidebar
        path_label = QLabel("📁 Data Path")
        path_label.setObjectName("PageSubtitle")
        path_label.setContentsMargins(16, 0, 16, 4)
        sb_lay.addWidget(path_label)

        path_val = QLabel(self._data_path)
        path_val.setObjectName("ModMeta")
        path_val.setContentsMargins(16, 0, 16, 0)
        path_val.setWordWrap(True)
        path_val.setFixedWidth(196)
        sb_lay.addWidget(path_val)

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

        self._mods_page = ModsPage(self._mod_manager, self._favorites_manager)
        self._mods_page.favorite_changed.connect(self._on_mod_favorite_changed)
        self._saves_page = SavesPage(self._save_manager)
        self._app_settings_page = AppSettingsPage(app_config_manager=self._app_config_manager)
        self._about_page = AboutPage()

        self._stack.addWidget(self._mods_page)         # Index 0 (Mod Manager)
        self._stack.addWidget(self._new_game_page)     # Index 1 (New Game)
        self._stack.addWidget(self._saves_page)        # Index 2 (Save Games)
        self._stack.addWidget(self._favorites_page)    # Index 3 (Favorites)
        self._stack.addWidget(self._all_mods_page)     # Index 4 (All Mods)
        self._stack.addWidget(self._maps_page)         # Index 5 (Maps)
        self._stack.addWidget(self._app_settings_page) # Index 6 (App Settings)
        self._stack.addWidget(self._about_page)        # Index 7 (About)

        root.addWidget(self._stack, stretch=1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.statusBar().showMessage(f"Data path: {self._data_path}")

        # Select first nav item
        self._switch_page(0)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _switch_page(self, index: int):
        self._stack.setCurrentIndex(index)
        
        # Trigger data population for specific pages
        if index == 1: # New Game
            self._new_game_page.populate_data()
            
        for i, btn in enumerate(self._nav_buttons):
            active = i == index
            btn.setProperty("active", "true" if active else "false")
            btn.setChecked(active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _open_folder(self):
        import subprocess
        subprocess.Popen(["xdg-open", self._data_path])

    def _on_mod_favorite_changed(self, mod_id: str, is_fav: bool):
        pass  # Main grids automatically refresh when toggled
