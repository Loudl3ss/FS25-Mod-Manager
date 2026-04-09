"""New Game wizard views with state persistence."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QGridLayout,
    QComboBox,
    QCheckBox,
    QMessageBox,
)

from ui.mod_grid import ModCard
from core.new_game_session import NewGameSession

# ─────────────────────────────────────────────────────────────────────────────
# Sub-Views
# ─────────────────────────────────────────────────────────────────────────────

class MapSelectionView(QWidget):
    """Step 1: Map selection with persistence."""
    
    request_next_step = pyqtSignal()

    def __init__(self, session: NewGameSession, favorites=None, parent=None):
        super().__init__(parent)
        self.session = session
        self._favorites = favorites
        self._cards: dict[str, ModCard] = {}
        self._mods_data: dict[str, object] = {}  # Store mod objects by name
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header section
        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(40, 40, 40, 20)
        
        title = QLabel("❶  Select Map")
        title.setObjectName("PageTitle")
        header_lay.addWidget(title)
        
        info = QLabel("Choose the location for your new farming career.")
        info.setObjectName("PageSubtitle")
        header_lay.addWidget(info)
        
        self.main_layout.addWidget(header)
        
        # Grid section (Scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(40, 0, 40, 0)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll)
        
        # Bottom Navigation
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b;")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(40, 16, 40, 16)
        
        nav_lay.addStretch()
        
        self.btn_next = QPushButton("Next  →")
        self.btn_next.setObjectName("PrimaryBtn")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next_clicked)
        nav_lay.addWidget(self.btn_next)
        
        self.main_layout.addWidget(nav_bar)

    def populate_maps(self, mods):
        """Filter mods for maps and populate the grid."""
        # Clear existing
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self._cards.clear()
        self._mods_data.clear()
        
        maps = [m for m in mods if m.category == "Map"]
        
        columns = 4
        for idx, mod in enumerate(maps):
            row = idx // columns
            col = idx % columns
            
            # Load icon
            pix = QPixmap()
            if mod.icon_data:
                pix.loadFromData(mod.icon_data)
            else:
                pix.load("ui/resources/default_mod.png")
            
            card = ModCard(
                mod.filename,
                pix,
                mod.title or mod.name,
                mod.version,
                is_favorite=self._favorites.is_favorite(mod.filename) if self._favorites else False,
                category=mod.category
            )
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.modClicked.connect(lambda m_id, c=card: self._on_card_clicked(m_id, c))
            card.favoriteToggled.connect(self._on_favorite_toggled)
            
            self.grid.addWidget(card, row, col)
            self._cards[mod.name] = card
            self._mods_data[mod.name] = mod

        # Restore previous selection if it exists
        if self.session.selected_map and self.session.selected_map in self._cards:
            self._restore_selection()

    def _on_favorite_toggled(self, mod_id: str, is_fav: bool):
        if not self._favorites:
            return
        self._favorites.set_favorite(mod_id, is_fav)

    def _on_card_clicked(self, mod_id: str, card: ModCard):
        """Handle card click - update selection."""
        self._deselect_all()
        self.session.selected_map = mod_id
        self._apply_selection_style(card)
        self.btn_next.setEnabled(True)

    def _deselect_all(self):
        """Remove highlight from all cards."""
        for card in self._cards.values():
            card.setStyleSheet("""
                ModCard {
                    background-color: transparent;
                    border: 2px solid #2e7d32;
                    border-radius: 12px;
                    padding: 0px;
                }
                ModCard:hover {
                    background-color: rgba(15, 23, 42, 0.4);
                    border: 2px solid #64dd17;
                }
            """)

    def _apply_selection_style(self, card: ModCard):
        """Apply white 3px border highlight to selected card."""
        card.setStyleSheet("""
            ModCard {
                background-color: rgba(15, 23, 42, 0.6);
                border: 3px solid #ffffff;
                border-radius: 12px;
                padding: 0px;
            }
            ModCard:hover {
                background-color: rgba(15, 23, 42, 0.8);
                border: 3px solid #ffffff;
            }
        """)

    def _restore_selection(self):
        """Highlight the previously selected map when view is shown."""
        if self.session.selected_map in self._cards:
            card = self._cards[self.session.selected_map]
            self._apply_selection_style(card)
            self.btn_next.setEnabled(True)

    def showEvent(self, event):
        """Called when view becomes visible."""
        super().showEvent(event)
        # Restore selection in case it was modified elsewhere
        if self.session.selected_map and self.session.selected_map in self._cards:
            self._restore_selection()

    def _on_next_clicked(self):
        if self.session.selected_map:
            self.request_next_step.emit()


class GameplaySettingsView(QWidget):
    """Step 2: Gameplay settings configuration."""
    
    request_next_step = pyqtSignal()
    request_previous_step = pyqtSignal()

    def __init__(self, session: NewGameSession, parent=None):
        super().__init__(parent)
        self.session = session
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(40, 40, 40, 20)
        
        title = QLabel("❷  Gameplay Settings")
        title.setObjectName("PageTitle")
        header_lay.addWidget(title)
        
        info = QLabel("Configure economic difficulty, seasons, and game rules.")
        info.setObjectName("PageSubtitle")
        header_lay.addWidget(info)
        
        layout.addWidget(header)
        
        # Content area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(40, 0, 40, 0)
        content_lay.setSpacing(12)
        
        # Difficulty setting
        diff_lbl = QLabel("Difficulty:")
        diff_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold;")
        content_lay.addWidget(diff_lbl)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Normal", "Hard"])
        self.difficulty_combo.currentTextChanged.connect(self._on_difficulty_changed)
        content_lay.addWidget(self.difficulty_combo)
        
        # Seasons setting
        seasons_lbl = QLabel("Seasons:")
        seasons_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; margin-top: 16px;")
        content_lay.addWidget(seasons_lbl)
        
        self.seasons_combo = QComboBox()
        self.seasons_combo.addItems(["Enabled", "Disabled"])
        self.seasons_combo.currentTextChanged.connect(self._on_seasons_changed)
        content_lay.addWidget(self.seasons_combo)
        
        # Economic system
        econ_lbl = QLabel("Economic System:")
        econ_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; margin-top: 16px;")
        content_lay.addWidget(econ_lbl)
        
        self.econ_combo = QComboBox()
        self.econ_combo.addItems(["Realistic", "Simplified"])
        self.econ_combo.currentTextChanged.connect(self._on_econ_changed)
        content_lay.addWidget(self.econ_combo)
        
        content_lay.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Navigation buttons
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b;")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(40, 16, 40, 16)
        
        self.btn_back = QPushButton("←  Back")
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.request_previous_step.emit)
        nav_lay.addWidget(self.btn_back)
        
        nav_lay.addStretch()
        
        self.btn_next = QPushButton("Next  →")
        self.btn_next.setObjectName("PrimaryBtn")
        self.btn_next.clicked.connect(self.request_next_step.emit)
        nav_lay.addWidget(self.btn_next)
        
        layout.addWidget(nav_bar)

    def _on_difficulty_changed(self, value):
        """Update session when difficulty changes."""
        self.session.settings["difficulty"] = value

    def _on_seasons_changed(self, value):
        """Update session when seasons change."""
        self.session.settings["seasons"] = value

    def _on_econ_changed(self, value):
        """Update session when economy setting changes."""
        self.session.settings["economicSystem"] = value

    def showEvent(self, event):
        """Restore previous settings when view is shown."""
        super().showEvent(event)
        if "difficulty" in self.session.settings:
            idx = self.difficulty_combo.findText(self.session.settings["difficulty"])
            if idx >= 0:
                self.difficulty_combo.setCurrentIndex(idx)
        
        if "seasons" in self.session.settings:
            idx = self.seasons_combo.findText(self.session.settings["seasons"])
            if idx >= 0:
                self.seasons_combo.setCurrentIndex(idx)
        
        if "economicSystem" in self.session.settings:
            idx = self.econ_combo.findText(self.session.settings["economicSystem"])
            if idx >= 0:
                self.econ_combo.setCurrentIndex(idx)


class ModLoadoutView(QWidget):
    """Step 3: Mod selection and game creation."""
    
    request_previous_step = pyqtSignal()
    game_created = pyqtSignal()  # Emitted when game is successfully created

    def __init__(self, session: NewGameSession, save_manager=None, mod_manager=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.save_manager = save_manager
        self.mod_manager = mod_manager
        self._mod_checkboxes: dict[str, QCheckBox] = {}
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(40, 40, 40, 20)
        
        title = QLabel("❸  Initial Mod Loadout")
        title.setObjectName("PageTitle")
        header_lay.addWidget(title)
        
        info = QLabel("Select the mods you want to enable for this savegame.")
        info.setObjectName("PageSubtitle")
        header_lay.addWidget(info)
        
        layout.addWidget(header)
        
        # Content area with mod list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.content_lay = QVBoxLayout(content)
        self.content_lay.setContentsMargins(40, 0, 40, 0)
        self.content_lay.setSpacing(8)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Navigation buttons
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b;")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(40, 16, 40, 16)
        
        self.btn_back = QPushButton("←  Back")
        self.btn_back.setObjectName("SecondaryBtn")
        self.btn_back.clicked.connect(self.request_previous_step.emit)
        nav_lay.addWidget(self.btn_back)
        
        nav_lay.addStretch()
        
        self.btn_create = QPushButton("Create Game")
        self.btn_create.setObjectName("PrimaryBtn")
        self.btn_create.clicked.connect(self._on_create_clicked)
        nav_lay.addWidget(self.btn_create)
        
        layout.addWidget(nav_bar)

    def populate_mods(self, mods):
        """Populate the list of available mods (non-maps)."""
        # Clear existing
        for checkbox in self._mod_checkboxes.values():
            checkbox.deleteLater()
        self._mod_checkboxes.clear()
        
        # Get non-map mods
        non_maps = [m for m in mods if m.category != "Map"]
        
        if not non_maps:
            label = QLabel("No additional mods available")
            label.setStyleSheet("color: #64748b;")
            self.content_lay.addWidget(label)
            return
        
        for mod in non_maps:
            checkbox = QCheckBox(f"{mod.title or mod.name} (v{mod.version})")
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #e2e8f0;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #1e293b;
                    border: 2px solid #475569;
                    border-radius: 4px;
                }
                QCheckBox::indicator:checked {
                    background-color: #22c55e;
                    border: 2px solid #16a34a;
                    border-radius: 4px;
                }
            """)
            
            # Check if this mod was previously selected
            if mod.name in self.session.selected_mods:
                checkbox.setChecked(True)
            
            checkbox.stateChanged.connect(lambda state, name=mod.name: self._on_mod_toggled(name, state))
            self.content_lay.addWidget(checkbox)
            self._mod_checkboxes[mod.name] = checkbox
        
        self.content_lay.addStretch()

    def _on_mod_toggled(self, mod_name: str, state):
        """Update session when a mod is toggled."""
        if state == 2:  # Qt.CheckState.Checked
            if mod_name not in self.session.selected_mods:
                self.session.selected_mods.append(mod_name)
        else:  # Unchecked
            if mod_name in self.session.selected_mods:
                self.session.selected_mods.remove(mod_name)

    def _on_create_clicked(self):
        """Create the new game save."""
        if not self.session.selected_map:
            QMessageBox.warning(self, "Error", "No map selected")
            return
        
        if not self.save_manager:
            QMessageBox.critical(self, "Error", "Save manager not available")
            return
        
        try:
            success, message = self.save_manager.finalize_new_game(self.session)
            if success:
                QMessageBox.information(self, "Success", message)
                self.session.reset()  # Reset for potential next wizard run
                self.game_created.emit()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create game: {str(e)}")

    def showEvent(self, event):
        """Update mod list when view is shown."""
        super().showEvent(event)
        if self.mod_manager:
            self.populate_mods(self.mod_manager.get_mods())


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
        
        self.mods_view = ModLoadoutView(self.session, save_manager, mod_manager)
        self.mods_view.request_previous_step.connect(lambda: self._switch_step(1))
        self.mods_view.game_created.connect(self.game_created.emit)
        
        self.new_game_stack.addWidget(self.map_view)       # 0
        self.new_game_stack.addWidget(self.settings_view)  # 1
        self.new_game_stack.addWidget(self.mods_view)      # 2
        
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

    def _switch_step(self, index: int):
        """Switch to a specific step in the wizard."""
        self.new_game_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._sub_nav_buttons):
            active = (i == index)
            btn.setProperty("active", "true" if active else "false")
            btn.setChecked(active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
