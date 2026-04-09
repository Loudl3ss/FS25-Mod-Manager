import math
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QFontMetrics, QPixmap, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QSizePolicy, QFrame, QPushButton, QGraphicsDropShadowEffect, QLayout
)


class ClippedThumbnail(QLabel):
    """Custom QLabel that clips its content with parameterizable rounded corners."""
    def __init__(self, corner_radius=8, parent=None):
        super().__init__(parent)
        self.corner_radius = corner_radius

    def paintEvent(self, event):
        if self.pixmap() and not self.pixmap().isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # The "Bleed" Trick: Expand rect slightly to draw under the border
            draw_rect = QRectF(self.rect()).adjusted(-1, -1, 1, 0)
            
            path = QPainterPath()
            path.addRoundedRect(draw_rect, float(self.corner_radius), float(self.corner_radius))
            
            painter.setClipPath(path)
            
            # Scaled pixmap following setScaledContents behavior
            scaled_pixmap = self.pixmap().scaled(
                self.size(), 
                Qt.AspectRatioMode.IgnoreAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(draw_rect.toRect(), scaled_pixmap)
            painter.end()
        else:
            super().paintEvent(event)


class ModCard(QFrame):
    """Custom PyQt6 widget representing a Mod Card."""
    
    modClicked = pyqtSignal(str)
    favoriteToggled = pyqtSignal(str, bool)

    def __init__(self, mod_id: str, thumbnail: QPixmap, name: str, version: str, is_favorite: bool=False, category: str="Mod", parent=None):
        super().__init__(parent)
        self.mod_id = mod_id
        self.category = category
        self._is_favorite = is_favorite
        self.setProperty("favorite", "true" if self._is_favorite else "false")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Styling
        self.setStyleSheet("""
            ModCard[favorite="true"] {
                background-color: transparent;
                border: 2px solid #39FF14;
                border-radius: 12px;
                padding: 0px;
            }
            ModCard[favorite="false"] {
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # Top: Thumbnail
        self.thumbnail_lbl = ClippedThumbnail(corner_radius=10)
        self.thumbnail_lbl.setFixedSize(150, 140)
        self.thumbnail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_lbl.setScaledContents(True)
        if self._is_favorite:
            self.thumbnail_lbl.setScaledContents(False)
            self.thumbnail_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.thumbnail_lbl.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        if not thumbnail.isNull():
            self.thumbnail_lbl.setPixmap(thumbnail)
        else:
            self.thumbnail_lbl.setText("🌾")
            self.thumbnail_lbl.setStyleSheet(self.thumbnail_lbl.styleSheet() + "font-size: 64px;")
            self.thumbnail_lbl.setScaledContents(False)

        layout.addWidget(self.thumbnail_lbl)

        # Category Badge overlay
        self.category_badge = QLabel(category.upper(), self)
        
        cat_lower = category.lower()
        if "map" in cat_lower:
            bg_hex = "#9c27b0"
        elif "tractor" in cat_lower:
            bg_hex = "#2e7d32"
        elif "trailer" in cat_lower:
            bg_hex = "#ef6c00"
        elif "script" in cat_lower:
            bg_hex = "#455a64"
        elif any(k in cat_lower for k in ["placeable", "shed", "silo", "factory", "animal"]):
            bg_hex = "#0277bd"
        else:
            bg_hex = "#006064"
            
        # Convert hex to rgba with 0.8 opacity
        r = int(bg_hex[1:3], 16)
        g = int(bg_hex[3:5], 16)
        b = int(bg_hex[5:7], 16)
        
        self.category_badge.setStyleSheet(f"""
            background-color: rgba({r}, {g}, {b}, 204);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
        """)
        # Ensure the badge size adjusts to its text
        self.category_badge.adjustSize()
        self.category_badge.move(6, 6)

        # Favorite Button overlay
        self.fav_btn = QPushButton("", self)
        self.fav_btn.setObjectName("FavoriteBtn")
        self.fav_btn.setFixedSize(28, 28)
        self.fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fav_btn.setStyleSheet("""
            QPushButton#FavoriteBtn {
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 4px;
            }
            QPushButton#FavoriteBtn[active="true"] {
                background-color: rgba(15, 23, 42, 0.8);
                border: 2px solid #39FF14;
            }
            QPushButton#FavoriteBtn:hover {
                background-color: rgba(0, 0, 0, 0.5);
            }
        """)
        
        self.fav_star_lbl = QLabel("★", self.fav_btn)
        self.fav_star_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fav_star_lbl.setFixedSize(28, 28)
        self.fav_star_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if self._is_favorite:
            self.fav_star_lbl.setStyleSheet("background: transparent; color: #FFD700; font-size: 20px; font-weight: bold; border: none;")
        else:
            self.fav_star_lbl.setStyleSheet("background: transparent; color: #FFD700; font-size: 18px; font-weight: normal; border: none;")

        self.fav_btn.setProperty("active", self._is_favorite)
        self.fav_btn.style().unpolish(self.fav_btn)
        self.fav_btn.style().polish(self.fav_btn)
        self.style().unpolish(self)
        self.style().polish(self)
        
        self.fav_effect = QGraphicsDropShadowEffect(self.fav_btn)
        self.fav_effect.setBlurRadius(10)
        self.fav_effect.setColor(QColor(57, 255, 20, 150))
        self.fav_effect.setOffset(0, 0)
        self.fav_btn.setGraphicsEffect(self.fav_effect)
        self.fav_effect.setEnabled(self._is_favorite)
        
        self.fav_btn.move(116, 6)
        self.fav_btn.clicked.connect(self._toggle_favorite)

        # Bottom: Text Container
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 8, 10, 8)
        text_layout.setSpacing(4)
        
        # Mod Name (Elided)
        font_name = QFont()
        font_name.setPointSize(10)
        metrics = QFontMetrics(font_name)
        elided_name = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 120)
        
        self.name_lbl = QLabel(elided_name)
        self.name_lbl.setFont(font_name)
        self.name_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(self.name_lbl)

        # Version
        font_version = QFont()
        font_version.setPointSize(8)
        self.version_lbl = QLabel(f"v{version}" if version else "v1.0")
        self.version_lbl.setFont(font_version)
        self.version_lbl.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
        self.version_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(self.version_lbl)

        layout.addLayout(text_layout)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.modClicked.emit(self.mod_id)

    def _toggle_favorite(self):
        self._is_favorite = not self._is_favorite
        self.fav_btn.setProperty("active", "true" if self._is_favorite else "false")
        self.setProperty("favorite", "true" if self._is_favorite else "false")
        self.fav_btn.style().unpolish(self.fav_btn)
        self.fav_btn.style().polish(self.fav_btn)
        self.style().unpolish(self)
        self.style().polish(self)
        
        if self._is_favorite:
            self.fav_star_lbl.setStyleSheet("background: transparent; color: #FFD700; font-size: 20px; font-weight: bold; border: none;")
        else:
            self.fav_star_lbl.setStyleSheet("background: transparent; color: #FFD700; font-size: 18px; font-weight: normal; border: none;")
            
        self.fav_effect.setEnabled(self._is_favorite)
        self.favoriteToggled.emit(self.mod_id, self._is_favorite)


class ResponsiveModGrid(QScrollArea):
    """A scroll area containing a responsive grid of ModCards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self.setWidget(self._container)
        
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._grid.setSpacing(12)
        
        self._cards = []
        self._card_width = 150 + 12 # width + spacing

    def add_mod(self, mod_id: str, thumbnail: QPixmap, name: str, version: str, is_favorite: bool=False, category: str="Mod") -> ModCard:
        """Dynamically add a ModCard to the grid."""
        card = ModCard(mod_id, thumbnail, name, version, is_favorite, category)
        self._cards.append(card)
        self._reflow()
        return card

    def clear_mods(self):
        """Remove all cards."""
        for card in self._cards:
            self._grid.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def _reflow(self):
        """Recalculate layout rows/columns based on current width."""
        if not self._cards:
            return
            
        # Determine available width
        available_width = self.viewport().width() - 16
        columns = max(1, available_width // self._card_width)

        # Clear existing layout items without deleting widgets
        for i in reversed(range(self._grid.count())):
            item = self._grid.takeAt(i)

        # Reassign positions
        for index, card in enumerate(self._cards):
            row = index // columns
            col = index % columns
            self._grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Add vertical spacer at the bottom to push items up
        self._grid.setRowStretch(self._grid.rowCount(), 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()
