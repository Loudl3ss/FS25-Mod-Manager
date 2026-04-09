"""Map selection page for New Game wizard."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.mod_grid import ModCard
from core.new_game_session import NewGameSession


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
                if not pix.loadFromData(mod.icon_data) or pix.isNull():
                    try:
                        from io import BytesIO
                        from PIL import Image
                        img = Image.open(BytesIO(mod.icon_data)).convert("RGBA")
                        qim = QImage(img.tobytes("raw", "RGBA"), img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                        pix = QPixmap.fromImage(qim)
                    except Exception:
                        pix = QPixmap()

            card = ModCard(
                mod.id,  # Use mod ID instead of filename
                pix,
                mod.title or mod.name,
                mod.version,
                is_favorite=self._favorites.is_favorite(mod.id) if self._favorites else False,  # Use ID
                category=mod.category
            )
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.modClicked.connect(lambda m_id, c=card: self._on_card_clicked(m_id, c))
            card.favoriteToggled.connect(self._on_favorite_toggled)
            
            self.grid.addWidget(card, row, col)
            self._cards[mod.id] = card  # Use ID as key
            self._mods_data[mod.id] = mod  # Use ID as key
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