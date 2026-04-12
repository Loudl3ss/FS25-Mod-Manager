"""New Game wizard main container."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.map_select_page import MapSelectionView
from ui.settings_select_page import GameplaySettingsView
from ui.mod_select_page import ModLoadoutView
from ui.success_message_page import SuccessMessageView
from core.new_game_session import NewGameSession


# ─────────────────────────────────────────────────────────────────────────────
# NewGameView (Main Wizard)
# ─────────────────────────────────────────────────────────────────────────────

class NewGameView(QWidget):
    """Parent wizard container managing all steps."""
    
    game_created = pyqtSignal()

    def __init__(self, mod_manager=None, save_manager=None, favorites_manager=None, parent=None):
        super().__init__(parent)
        self._mod_manager = mod_manager
        self._save_manager = save_manager
        self._favorites_manager = favorites_manager
        
        # Create session
        self.session = NewGameSession()
        
        # Main layout (Secondary Sidebar + Content Stack)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # ── Secondary Sidebar ────────────────────────────────────────
        self.sub_sidebar = QFrame()
        self.sub_sidebar.setObjectName("SubSidebar")
        self.sub_sidebar.setFixedWidth(200)
        self.sub_sidebar.setStyleSheet("""
            QFrame#SubSidebar {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            QPushButton#SubNavBtn {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 12px 20px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#SubNavBtn:hover {
                background-color: #1e293b;
                color: #e2e8f0;
            }
            QPushButton#SubNavBtn[active="true"] {
                color: #4ade80;
                background-color: rgba(74, 222, 128, 0.1);
                border-right: 3px solid #4ade80;
            }
        """)
        
        self.sub_sidebar_layout = QVBoxLayout(self.sub_sidebar)
        self.sub_sidebar_layout.setContentsMargins(0, 20, 0, 0)
        self.sub_sidebar_layout.setSpacing(2)
        
        self._sub_nav_buttons: list[QPushButton] = []
        
        steps = [
            ("❶  Map", 0),
            ("❷  Settings", 1),
            ("❸  Mods", 2),
            ("✅  Success", 3),
        ]
        
        for text, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("SubNavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._switch_step(i))
            self.sub_sidebar_layout.addWidget(btn)
            self._sub_nav_buttons.append(btn)
            
        self.sub_sidebar_layout.addStretch()
        
        # ── Content Area ─────────────────────────────────────────────
        self.new_game_stack = QStackedWidget()
        self.new_game_stack.setObjectName("NewGameStack")
        
        # Create views with session reference
        self.map_view = MapSelectionView(self.session, self._favorites_manager)
        self.map_view.request_next_step.connect(self._on_map_next)
        
        self.settings_view = GameplaySettingsView(self.session)
        self.settings_view.request_next_step.connect(self._on_settings_next)
        self.settings_view.request_previous_step.connect(lambda: self._switch_step(0))
        
        self.mods_view = ModLoadoutView(self.session, save_manager, mod_manager, self._favorites_manager)
        self.mods_view.request_previous_step.connect(lambda: self._switch_step(1))
        self.mods_view.game_created.connect(self._on_game_created)
        
        self.success_view = SuccessMessageView()
        self.success_view.wizard_completed.connect(self.game_created.emit)
        
        self.new_game_stack.addWidget(self.map_view)       # 0
        self.new_game_stack.addWidget(self.settings_view)  # 1
        self.new_game_stack.addWidget(self.mods_view)      # 2
        self.new_game_stack.addWidget(self.success_view)   # 3
        
        # Assemble
        self.main_layout.addWidget(self.sub_sidebar)
        self.main_layout.addWidget(self.new_game_stack)
        
        # Select first step
        self._switch_step(0)

    def populate_data(self):
        """Initial population of game data."""
        if self._mod_manager:
            self.map_view.populate_maps(self._mod_manager.get_mods())
            self.mods_view.populate_mods(self._mod_manager.get_mods())

    def _on_map_next(self):
        """Advance from map selection to settings."""
        self._switch_step(1)

    def _on_settings_next(self):
        """Advance from settings to mods."""
        self._switch_step(2)

    def _on_game_created(self):
        """Advance from mods to success page."""
        self._switch_step(3)

    def _switch_step(self, index: int):
        """Switch to a specific step in the wizard."""
        self.new_game_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._sub_nav_buttons):
            active = (i == index)
            btn.setProperty("active", "true" if active else "false")
            btn.setChecked(active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
