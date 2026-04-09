"""Favorite mod grid implementation."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QScrollArea, QSizePolicy, QWidget

from ui.mod_grid import ModCard


class FavoriteModGrid(QScrollArea):
    """A horizontal scroll area for favorite mod cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMaximumHeight(210)

        self._container = QWidget()
        self._container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setWidget(self._container)

        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._cards = []

    def add_mod(
        self,
        mod_id: str,
        thumbnail: QPixmap,
        name: str,
        version: str,
        is_favorite: bool = False,
        category: str = "Mod",
    ) -> ModCard:
        """Add a ModCard to the horizontal layout."""
        card = ModCard(mod_id, thumbnail, name, version, is_favorite, category)
        self._cards.append(card)
        self._layout.addWidget(card)
        return card

    def clear_mods(self):
        """Remove all cards."""
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
