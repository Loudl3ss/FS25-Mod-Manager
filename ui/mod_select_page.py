"""Mod selection page for New Game wizard."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
)

from core.mod_manager import ModInfo
from core.new_game_session import NewGameSession
from core.thumbnail_loader import ThumbnailLoader
from ui.mod_grid import ModCard, ResponsiveModGrid


class ModLoadoutView(QWidget):
    """Step 3: Mod selection and game creation."""

    request_previous_step = pyqtSignal()
    game_created = pyqtSignal()  # Emitted when game is successfully created

    def __init__(self, session: NewGameSession, save_manager=None, mod_manager=None, favorites_manager=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.save_manager = save_manager
        self.mod_manager = mod_manager
        self.favorites_manager = favorites_manager
        self._mod_cards: dict[str, ModCard] = {}
        self._mod_by_id: dict[str, ModInfo] = {}

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

        hint = QLabel("Tip: Favorites from Mod Manager are preselected. Click any card to toggle selection.")
        hint.setStyleSheet("color: #94a3b8;")
        header_lay.addWidget(hint)

        self._selected_count_lbl = QLabel("Selected: 0 mods")
        self._selected_count_lbl.setStyleSheet("color: #7dd3fc; font-weight: 600;")
        header_lay.addWidget(self._selected_count_lbl)

        layout.addWidget(header)

        self._empty_lbl = QLabel("No additional mods available")
        self._empty_lbl.setStyleSheet("color: #64748b;")
        self._empty_lbl.setContentsMargins(40, 0, 40, 0)
        self._empty_lbl.hide()
        layout.addWidget(self._empty_lbl)

        self._favorites_title = QLabel("Favorites")
        self._favorites_title.setObjectName("PageSubtitle")
        self._favorites_title.setContentsMargins(40, 0, 40, 8)
        layout.addWidget(self._favorites_title)

        self._favorites_grid = ResponsiveModGrid()
        self._favorites_grid.setStyleSheet("background: transparent;")
        self._favorites_grid.setViewportMargins(30, 0, 0, 0)
        self._favorites_grid.setMinimumHeight(240)
        layout.addWidget(self._favorites_grid)

        self._fav_gap = QWidget()
        self._fav_gap.setFixedHeight(30)
        layout.addWidget(self._fav_gap)

        self._others_title = QLabel("All Other Mods")
        self._others_title.setObjectName("PageSubtitle")
        self._others_title.setContentsMargins(40, 0, 40, 8)
        layout.addWidget(self._others_title)

        self._other_grid = ResponsiveModGrid()
        self._other_grid.setStyleSheet("background: transparent;")
        self._other_grid.setViewportMargins(30, 0, 0, 0)
        layout.addWidget(self._other_grid, stretch=1)

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
        self.btn_create.setStyleSheet(
            "background-color: #16a34a;"
            "border: 1px solid #4ade80;"
            "color: #ffffff;"
            "font-weight: 600;"
            "padding: 8px 20px;"
            "border-radius: 8px;"
        )
        self.btn_create.clicked.connect(self._on_create_clicked)
        nav_lay.addWidget(self.btn_create)

        layout.addWidget(nav_bar)

    def populate_mods(self, mods):
        """Populate the card grid of available mods (non-maps)."""
        self._favorites_grid.clear_mods()
        self._other_grid.clear_mods()
        self._mod_cards.clear()
        self._mod_by_id.clear()

        non_maps = [m for m in mods if m.category != "Map"]
        self._mod_by_id = {m.id: m for m in non_maps}

        if not non_maps:
            self._empty_lbl.show()
            self._favorites_title.hide()
            self._favorites_grid.hide()
            self._fav_gap.hide()
            self._others_title.hide()
            self._other_grid.hide()
            self.session.selected_mods = []
            self._update_selected_counter()
            return

        self._empty_lbl.hide()
        self._others_title.show()
        self._other_grid.show()

        available_ids = {m.id for m in non_maps}
        current_selection = [mid for mid in self.session.selected_mods if mid in available_ids]

        # First load defaults: preselect favorites from Mod Manager.
        favorite_ids = set()
        if self.favorites_manager:
            favorite_ids = {m.id for m in non_maps if self.favorites_manager.is_favorite(m.id)}

        if not current_selection and favorite_ids:
            current_selection = [m.id for m in non_maps if m.id in favorite_ids]

        self.session.selected_mods = current_selection
        self._update_selected_counter()

        favorites = [m for m in non_maps if m.id in favorite_ids]
        others = [m for m in non_maps if m.id not in favorite_ids]

        has_favorites = len(favorites) > 0
        self._favorites_title.setVisible(has_favorites)
        self._favorites_grid.setVisible(has_favorites)
        self._fav_gap.setVisible(has_favorites)

        for mod in favorites:
            self._add_mod_card(self._favorites_grid, mod)

        for mod in others:
            self._add_mod_card(self._other_grid, mod)

    def _add_mod_card(self, target_grid: ResponsiveModGrid, mod: ModInfo):
        """Create and wire a selectable card in a target grid."""
        thumbnail = ThumbnailLoader.obtain_local_pixmap(
            mod.icon_data,
            mod_id=mod.id,
            thumbnail_id=getattr(mod, "thumbnail_id", ""),
        )
        card = target_grid.add_mod(
            mod.id,
            thumbnail,
            mod.title or mod.name,
            mod.version,
            False,
            mod.category,
            thumbnail_id=getattr(mod, "thumbnail_id", ""),
        )
        if hasattr(card, "fav_btn"):
            card.fav_btn.hide()
        card.modClicked.connect(self._on_card_clicked)
        self._mod_cards[mod.id] = card
        self._apply_selected_style(card, mod.id in self.session.selected_mods)

    def _on_card_clicked(self, mod_id: str):
        if mod_id in self.session.selected_mods:
            self.session.selected_mods.remove(mod_id)
            self._apply_selected_style(self._mod_cards[mod_id], False)
            self._update_selected_counter()
            return

        self.session.selected_mods.append(mod_id)
        self._apply_selected_style(self._mod_cards[mod_id], True)
        self._update_selected_counter()

    def _update_selected_counter(self):
        count = len(self.session.selected_mods)
        suffix = "mod" if count == 1 else "mods"
        self._selected_count_lbl.setText(f"Selected: {count} {suffix}")

    @staticmethod
    def _apply_selected_style(card: ModCard, selected: bool):
        card.setProperty("selectedForGame", "true" if selected else "false")
        style = card.style()
        if style is not None:
            style.unpolish(card)
            style.polish(card)

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