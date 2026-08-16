"""Map selection page for New Game wizard."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.thumbnail_loader import ThumbnailLoader
from ui.mod_grid import ModCard
from core.new_game_session import NewGameSession
from ui.assets import Icons


class MapSelectionView(QWidget):
    """Step 1: Map selection with persistence."""

    request_next_step = pyqtSignal()
    map_selected = pyqtSignal()

    def __init__(self, session: NewGameSession, favorites=None, parent=None):
        super().__init__(parent)
        self.session = session
        self._favorites = favorites
        self._cards: dict[str, ModCard] = {}
        self._mods_data: dict[str, object] = {}  # Store mod objects by name
        self._last_multi_fav_signature: tuple[str, ...] | None = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setObjectName("WizardTopNav")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(24, 12, 24, 12)

        step_label = QLabel("Step 1 of 3")
        step_label.setObjectName("WizardStepLabel")
        nav_lay.addWidget(step_label)

        nav_lay.addStretch()

        self.btn_back = QPushButton("← Back")
        self.btn_back.setObjectName("WizardNavSecondaryBtn")
        self.btn_back.setEnabled(False)
        nav_lay.addWidget(self.btn_back)

        self.btn_next = QPushButton("Next →")
        self.btn_next.setObjectName("WizardNavPrimaryBtn")
        self.btn_next.setEnabled(False)
        self.btn_next.clicked.connect(self._on_next_clicked)
        nav_lay.addWidget(self.btn_next)

        # Header section
        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(40, 40, 40, 20)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        title_icon = QLabel()
        title_icon.setPixmap(Icons.get_qicon(Icons.COUNTER_1).pixmap(22, 22))
        title_row.addWidget(title_icon)

        title = QLabel("Select Map")
        title.setObjectName("PageTitle")
        title_row.addWidget(title)
        title_row.addStretch(1)
        header_lay.addLayout(title_row)

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
        self.main_layout.addWidget(nav_bar)

    def populate_maps(self, mods):
        """Filter mods for maps and populate the grid."""
        # Clear existing
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._cards.clear()
        self._mods_data.clear()

        maps = [m for m in mods if m.category == "Map"]
        favorite_map_ids = [m.id for m in maps if self._favorites and self._favorites.is_favorite(m.id)]

        if not maps:
            # Without this the grid is simply blank, which reads as "the app
            # failed to find my game" rather than "you have no map mods".
            empty = QLabel(
                "No map mods installed.\n\n"
                f"{len(mods)} mod(s) were found, but none of them is a map.\n"
                "Install a map mod into your mods folder, or browse for one in "
                "Online Mods, then press Refresh."
            )
            empty.setObjectName("EmptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            self.grid.addWidget(empty, 0, 0)
            # Nothing selectable, so drop any stale selection from a previous
            # scan instead of leaving Next enabled on a map that is now gone.
            self.session.selected_map = None
            self.btn_next.setEnabled(False)
            self._last_multi_fav_signature = None
            return

        columns = 4
        for idx, mod in enumerate(maps):
            row = idx // columns
            col = idx % columns

            pix = ThumbnailLoader.obtain_local_pixmap(
                mod.icon_data,
                mod_id=mod.id,
                thumbnail_id=mod.thumbnail_id,
            )

            card = ModCard(
                mod.id,  # Use mod ID instead of filename
                pix,
                mod.title or mod.name,
                mod.version,
                is_favorite=self._favorites.is_favorite(mod.id) if self._favorites else False,  # Use ID
                category=mod.category,
                thumbnail_id=mod.thumbnail_id,
            )
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.modClicked.connect(lambda m_id, c=card: self._on_card_clicked(m_id, c))
            card.favoriteToggled.connect(self._on_favorite_toggled)
            
            self.grid.addWidget(card, row, col)
            self._cards[mod.id] = card  # Use ID as key
            self._mods_data[mod.id] = mod  # Use ID as key

        # Favorite-aware preselection rules:
        # - exactly 1 favorite map => preselect it
        # - 2+ favorite maps => clear selection and show guidance message
        # - no favorite maps => keep previous selection if valid
        if len(favorite_map_ids) == 1 and favorite_map_ids[0] in self._cards:
            self._deselect_all()
            self.session.selected_map = favorite_map_ids[0]
            self._apply_selection_style(self._cards[favorite_map_ids[0]])
            self.btn_next.setEnabled(True)
            self.map_selected.emit()
            self._last_multi_fav_signature = None
        elif len(favorite_map_ids) >= 2:
            self._deselect_all()
            self.session.selected_map = None
            self.btn_next.setEnabled(False)
            signature = tuple(sorted(favorite_map_ids))
            if self._last_multi_fav_signature != signature:
                self._last_multi_fav_signature = signature
                QMessageBox.information(
                    self,
                    "Map Selection",
                    "Only one favorite map can be used for auto-selection. "
                    "Please keep only one map as favorite.",
                )
        else:
            self._last_multi_fav_signature = None
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
        self.map_selected.emit()

    def _deselect_all(self):
        """Remove highlight from all cards."""
        for card in self._cards.values():
            card.setStyleSheet("""
                ModCard {
                    background-color: transparent;
                    border: 2px solid #3f7d51;
                    border-radius: 12px;
                    padding: 0px;
                }
                ModCard:hover {
                    background-color: rgba(15, 23, 42, 0.4);
                    border: 2px solid #6bb07d;
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
            self.map_selected.emit()

    def showEvent(self, event):
        """Called when view becomes visible."""
        super().showEvent(event)
        # Restore selection in case it was modified elsewhere
        if self.session.selected_map and self.session.selected_map in self._cards:
            self._restore_selection()

    def _on_next_clicked(self):
        if self.session.selected_map:
            self.request_next_step.emit()
            return
        QMessageBox.information(self, "Select Map", "Please select a map before continuing.")