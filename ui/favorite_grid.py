"""Favorite mod grid implementation."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QScrollArea, QSizePolicy, QWidget

from ui.flow_layout import FlowLayout
from ui.mod_grid import ModCard


class FavoriteModGrid(QScrollArea):
    """A responsive flow grid for favorite mod cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMaximumHeight(210)

        self._container = QWidget()
        self._container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setWidget(self._container)

        self._flow = FlowLayout(self._container, margin=8, hSpacing=12, vSpacing=12)

        self._cards = []

    def add_mod(
        self,
        mod_id: str,
        thumbnail: QPixmap,
        name: str,
        version: str,
        is_favorite: bool = False,
        category: str = "Mod",
        thumbnail_id: str = "",
    ) -> ModCard:
        """Add a ModCard to the responsive flow layout."""
        card = ModCard(
            mod_id,
            thumbnail,
            name,
            version,
            is_favorite,
            category,
            thumbnail_id=thumbnail_id,
        )
        self._cards.append(card)
        self._flow.addWidget(card)
        return card

    def clear_mods(self):
        """Remove all cards."""
        for card in self._cards:
            self._flow.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._container.updateGeometry()
