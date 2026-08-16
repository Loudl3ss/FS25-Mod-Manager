"""New Game wizard main container."""
import re

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.success_message_page import GameCreatedDialog
from ui.assets import Icons

from ui.map_select_page import MapSelectionView
from ui.settings_select_page import GameplaySettingsView
from ui.mod_select_page import ModLoadoutView
from ui.style_helpers import set_bool_property
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
        self._step_default_icons = [
            Icons.COUNTER_1,
            Icons.COUNTER_2,
            Icons.COUNTER_3,
        ]
        self._step_done_icon = Icons.SUCESFULL
        self._step_completed = [False, False, False]
        
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
                background-color: #0b0e12;
                border-right: 1px solid #161a21;
            }
            QPushButton#SubNavBtn {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 10px 14px;
                padding-left: 12px;
                color: #8b94a1;
                font-size: 13px;
                font-weight: 400;
                margin: 2px 8px;
                border-radius: 8px;
            }
            QPushButton#SubNavBtn:hover {
                background-color: #161a21;
                color: #d5dbe3;
            }
            QPushButton#SubNavBtn[active="true"] {
                font-weight: 600;
                color: #5a9e6b;
                background-color: rgba(74, 222, 128, 0.1);
                border-right: 3px solid #5a9e6b;
            }
        """)
        
        self.sub_sidebar_layout = QVBoxLayout(self.sub_sidebar)
        self.sub_sidebar_layout.setContentsMargins(0, 20, 0, 0)
        self.sub_sidebar_layout.setSpacing(2)
        
        self._sub_nav_buttons: list[QPushButton] = []
        
        steps = [
            ("Select Map", self._step_default_icons[0], 0),
            ("Gameplay Settings", self._step_default_icons[1], 1),
            ("Mods", self._step_default_icons[2], 2),
        ]
        
        for text, icon_name, idx in steps:
            btn = QPushButton(text)
            btn.setObjectName("SubNavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(Icons.get_qicon(icon_name))
            btn.setIconSize(QSize(20, 20))
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
        self.map_view.map_selected.connect(self._on_map_selected)
        
        self.settings_view = GameplaySettingsView(self.session)
        self.settings_view.request_next_step.connect(self._on_settings_next)
        self.settings_view.request_previous_step.connect(lambda: self._switch_step(0))
        
        self.mods_view = ModLoadoutView(self.session, save_manager, mod_manager, self._favorites_manager)
        self.mods_view.request_previous_step.connect(lambda: self._switch_step(1))
        self.mods_view.game_created.connect(self._on_game_created)
        
        self.new_game_stack.addWidget(self.map_view)       # 0
        self.new_game_stack.addWidget(self.settings_view)  # 1
        self.new_game_stack.addWidget(self.mods_view)      # 2
        
        # Assemble
        self.main_layout.addWidget(self.sub_sidebar)
        self.main_layout.addWidget(self.new_game_stack)
        
        # Select first step
        self._refresh_step_icons()
        self._switch_step(0)

    def populate_data(self):
        """Initial population of game data."""
        if self._mod_manager:
            self.map_view.populate_maps(self._mod_manager.get_mods())
            self.mods_view.populate_mods(self._mod_manager.get_mods())

    def open_map_step(self):
        """Open wizard at step 1 (map selection)."""
        self.populate_data()
        self._step_completed = [bool(self.session.selected_map), False, False]
        self._refresh_step_icons()
        self._switch_step(0)

    def _on_map_selected(self):
        """Mark map step completed as soon as map selection is made."""
        self._set_step_completed(0, True)

    def _on_map_next(self):
        """Advance from map selection to settings."""
        self._set_step_completed(0, True)
        self._switch_step(1)

    def _on_settings_next(self):
        """Advance from settings to mods."""
        self._set_step_completed(1, True)
        self._switch_step(2)

    def _on_game_created(self, message: str):
        """Show styled success dialog and handle user's next action."""
        self._step_completed = [True, True, True]
        self._refresh_step_icons()

        match = re.search(r"save slot\s+(\d+)", message, flags=re.IGNORECASE)
        slot = int(match.group(1)) if match else 1
        save_name = self.session.settings.get("savegameName", "My Farm")

        dlg = GameCreatedDialog(save_name, slot, parent=self)
        dlg.exec()

        if dlg.result_action() == "another":
            self.session.reset()
            self._step_completed = [False, False, False]
            self._refresh_step_icons()
            self._switch_step(0)
        else:
            self._step_completed = [False, False, False]
            self._refresh_step_icons()
            self._switch_step(0)
            self.game_created.emit()

    def _switch_step(self, index: int):
        """Switch to a specific step in the wizard."""
        self.new_game_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._sub_nav_buttons):
            active = (i == index)
            set_bool_property(btn, "active", active)
            btn.setChecked(active)

    def _set_step_completed(self, index: int, completed: bool):
        if 0 <= index < len(self._step_completed):
            if self._step_completed[index] != completed:
                self._step_completed[index] = completed
                self._refresh_step_icons()

    def _refresh_step_icons(self):
        for i, btn in enumerate(self._sub_nav_buttons):
            icon_name = self._step_done_icon if self._step_completed[i] else self._step_default_icons[i]
            btn.setIcon(Icons.get_qicon(icon_name))
            btn.setIconSize(QSize(20, 20))
