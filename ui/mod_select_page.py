"""Mod selection page for New Game wizard."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
)

from core.new_game_session import NewGameSession


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
            if mod.id in self.session.selected_mods:
                checkbox.setChecked(True)

            checkbox.stateChanged.connect(lambda state, mod_id=mod.id: self._on_mod_toggled(mod_id, state))
            self.content_lay.addWidget(checkbox)
            self._mod_checkboxes[mod.id] = checkbox

        self.content_lay.addStretch()

    def _on_mod_toggled(self, mod_id: str, state):
        """Update session when a mod is toggled."""
        if state == 2:  # Qt.CheckState.Checked
            if mod_id not in self.session.selected_mods:
                self.session.selected_mods.append(mod_id)
        else:  # Unchecked
            if mod_id in self.session.selected_mods:
                self.session.selected_mods.remove(mod_id)

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
                # QMessageBox.information(self, "Success", message)
                self.session.reset()  # Reset for potential next wizard run
                self.game_created.emit()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create game: {str(e)}")