import math
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QRectF, QSize
from PyQt6.QtGui import QFont, QFontMetrics, QPixmap, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QLabel, QScrollArea, QVBoxLayout, QWidget, QSizePolicy, QFrame, QPushButton, QGraphicsDropShadowEffect, QLayout
)

from core.thumbnail_loader import ThumbnailLoader
from ui.flow_layout import FlowLayout
from ui.assets import Icons
from ui.style_helpers import apply_card_shadow, refresh_widget_style, set_bool_property


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
            
            # Keep full thumbnail visible (no side-cropping) inside rounded bounds.
            draw_rect = QRectF(self.rect())
            
            path = QPainterPath()
            path.addRoundedRect(draw_rect, float(self.corner_radius), float(self.corner_radius))
            
            painter.setClipPath(path)
            
            # Cover the full cell – expand+crop so all thumbnails align uniformly.
            scaled_pixmap = ThumbnailLoader.obtain_scaled_pixmap(
                self.pixmap(),
                width=self.size().width(),
                height=self.size().height(),
                keep_aspect_by_expanding=True,
            )
            
            # Center the pixmap in the draw rect
            rect = draw_rect.toRect()
            pix_rect = scaled_pixmap.rect()
            x = rect.x() + (rect.width() - pix_rect.width()) // 2
            y = rect.y() + (rect.height() - pix_rect.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
        else:
            super().paintEvent(event)


class ModCard(QFrame):
    """Custom PyQt6 widget representing a Mod Card."""
    
    modClicked = pyqtSignal(str)
    favoriteToggled = pyqtSignal(str, bool)

    def __init__(self, mod_id: str, thumbnail: QPixmap, name: str, version: str, is_favorite: bool=False, category: str="Mod", thumbnail_id: str = "", show_favorite: bool = True, parent=None):
        super().__init__(parent)
        self._show_favorite = show_favorite
        self.card_id = f"mod-card-{mod_id}"
        self.mod_id = mod_id
        self.thumbnail_id = thumbnail_id
        self.category = category
        self._is_favorite = is_favorite
        self.setObjectName(self.card_id)
        self.setProperty("cardId", self.card_id)
        self.setProperty("modId", self.mod_id)
        self.setProperty("thumbnailId", self.thumbnail_id)
        self.setProperty("favorite", "true" if self._is_favorite else "false")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(126, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Glass card: translucent fill over the window gradient, hairline
        # border, one accent colour reserved for favourite/selected states.
        self.setStyleSheet("""
            ModCard[favorite="false"] {
                background-color: rgba(255, 255, 255, 0.035);
                border: 1px solid rgba(255, 255, 255, 0.065);
                border-radius: 10px;
                padding: 0px;
            }
            ModCard[favorite="true"] {
                background-color: rgba(90, 158, 107, 0.10);
                border: 1px solid rgba(122, 194, 141, 0.40);
                border-radius: 10px;
                padding: 0px;
            }
            ModCard:hover {
                background-color: rgba(255, 255, 255, 0.16);
                border: 1px solid rgba(255, 255, 255, 0.30);
            }
            /* After :hover on purpose. Equal specificity means the last rule
               wins, and selection must survive the mouse resting on the card
               right after the click that selected it. */
            ModCard[selectedForGame="true"],
            ModCard[selectedForGame="true"]:hover {
                background-color: rgba(255, 255, 255, 0.035);
                border: 1px solid #7cc28d;
            }
        """)
        apply_card_shadow(self, blur=18, y=4, alpha=90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        # Top: Thumbnail
        self.thumbnail_lbl = ClippedThumbnail(corner_radius=9)
        self.thumbnail_lbl.setFixedSize(120, 144)
        self.thumbnail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_lbl.setScaledContents(True)
        if self._is_favorite:
            self.thumbnail_lbl.setScaledContents(False)
            self.thumbnail_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.thumbnail_lbl.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.thumbnail_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if not thumbnail.isNull() and not thumbnail.size().isEmpty():
            self.thumbnail_lbl.setPixmap(thumbnail)
        else:
            # Show default icon based on category
            if category.lower() == "map":
                self.thumbnail_lbl.setText("🗺️")
            else:
                self.thumbnail_lbl.setText("🌾")
            self.thumbnail_lbl.setStyleSheet(self.thumbnail_lbl.styleSheet() + "font-size: 44px;")
            self.thumbnail_lbl.setScaledContents(False)

        layout.addWidget(self.thumbnail_lbl)

        # Category Badge overlay
        self.category_badge = QLabel(category, self)
        
        cat_lower = category.lower()
        if "map" in cat_lower:
            bg_hex = "#8f6ba8"
        elif "tractor" in cat_lower:
            bg_hex = "#3f7d51"
        elif "trailer" in cat_lower:
            bg_hex = "#c07a3a"
        elif "script" in cat_lower:
            bg_hex = "#414b59"
        elif any(k in cat_lower for k in ["placeable", "shed", "silo", "factory", "animal"]):
            bg_hex = "#3f5f80"
        else:
            bg_hex = "#2f5560"
            
        # Convert hex to rgba with 0.8 opacity
        r = int(bg_hex[1:3], 16)
        g = int(bg_hex[3:5], 16)
        b = int(bg_hex[5:7], 16)
        
        self.category_badge.setStyleSheet(f"""
            background-color: rgba({r}, {g}, {b}, 204);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 8px;
            font-weight: 600;
        """)
        # Ensure the badge size adjusts to its text
        self.category_badge.adjustSize()
        self.category_badge.move(8, 8)
        self.category_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Favorite Button overlay with SVG icon
        self.fav_btn = None
        self.fav_effect = None
        if self._show_favorite:
            self.fav_btn = QPushButton("", self)
            self.fav_btn.setObjectName("FavoriteBtn")
            self.fav_btn.setFixedSize(22, 22)
            self.fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.fav_btn.setStyleSheet("""
                QPushButton#FavoriteBtn {
                    background-color: transparent;
                    border: 2px solid transparent;
                    border-radius: 4px;
                    padding: 0px;
                    min-width: 0px;
                }
                QPushButton#FavoriteBtn[active="true"] {
                    background-color: rgba(15, 23, 42, 0.8);
                    border: 2px solid #5a9e6b;
                }
                QPushButton#FavoriteBtn:hover {
                    background-color: rgba(0, 0, 0, 0.5);
                }
            """)

            # Set SVG icon based on favorite state
            if self._is_favorite:
                self.fav_btn.setIcon(Icons.get_qicon(Icons.STAR))
            else:
                self.fav_btn.setIcon(Icons.get_qicon(Icons.STAR_OUTLINE))
            self.fav_btn.setIconSize(QSize(20, 20))

            set_bool_property(self.fav_btn, "active", self._is_favorite)
            refresh_widget_style(self)

            self.fav_effect = QGraphicsDropShadowEffect(self.fav_btn)
            self.fav_effect.setBlurRadius(10)
            self.fav_effect.setColor(QColor(57, 255, 20, 150))
            self.fav_effect.setOffset(0, 0)
            self.fav_btn.setGraphicsEffect(self.fav_effect)
            self.fav_effect.setEnabled(self._is_favorite)

            self.fav_btn.move(97, 8)
            self.fav_btn.clicked.connect(self._toggle_favorite)

        # Caption overlaid on the artwork instead of a separate strip below it:
        # the card stays smaller while the thumbnail keeps its full size.
        caption = QWidget(self)
        caption.setGeometry(3, self.height() - 45, self.width() - 6, 42)
        caption.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 rgba(10, 13, 17, 0),
                                        stop:0.45 rgba(10, 13, 17, 190),
                                        stop:1 rgba(10, 13, 17, 240));
            border: none;
            border-bottom-left-radius: 9px;
            border-bottom-right-radius: 9px;
        """)
        caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        caption_lay = QVBoxLayout(caption)
        caption_lay.setContentsMargins(8, 4, 8, 5)
        caption_lay.setSpacing(0)

        font_name = QFont()
        font_name.setPointSize(9)
        font_name.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(font_name)

        self.name_lbl = QLabel(metrics.elidedText(name, Qt.TextElideMode.ElideRight, 104))
        self.name_lbl.setFont(font_name)
        self.name_lbl.setStyleSheet("color: #f2f5f9; border: none; background: transparent;")
        self.name_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        caption_lay.addWidget(self.name_lbl)

        font_version = QFont()
        font_version.setPointSize(7)
        self.version_lbl = QLabel(f"v{version}" if version else "")
        self.version_lbl.setFont(font_version)
        self.version_lbl.setStyleSheet("color: #a8b1bd; border: none; background: transparent;")
        self.version_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        caption_lay.addWidget(self.version_lbl)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.modClicked.emit(self.mod_id)
        # Stop here: an unaccepted press bubbles up to the grid, which reads it
        # as a click on empty space and clears the selection we just made.
        event.accept()

    def set_selected(self, selected: bool):
        set_bool_property(self, "selectedForGame", selected)

    def _toggle_favorite(self):
        if not self._show_favorite or self.fav_btn is None:
            return
        self._is_favorite = not self._is_favorite
        set_bool_property(self.fav_btn, "active", self._is_favorite)
        set_bool_property(self, "favorite", self._is_favorite)
        
        # Update SVG icon based on favorite state
        if self._is_favorite:
            self.fav_btn.setIcon(Icons.get_qicon(Icons.STAR))
        else:
            self.fav_btn.setIcon(Icons.get_qicon(Icons.STAR_OUTLINE))
            
        if self.fav_effect is not None:
            self.fav_effect.setEnabled(self._is_favorite)
        self.favoriteToggled.emit(self.mod_id, self._is_favorite)


class ResponsiveModGrid(QScrollArea):
    """A scroll area containing a responsive grid of ModCards."""

    backgroundClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self.setWidget(self._container)

        # Flow layout keeps cards left-aligned with stable spacing.
        self._flow = FlowLayout(self._container, margin=8, hSpacing=12, vSpacing=12)
        
        self._cards = []
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """A click on empty space clears the selection.

        The filter sits on the viewport because that is what receives mouse
        events in a scroll area. Cards accept their own presses, so anything
        arriving here landed outside them.
        """
        if obj is self.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            self.backgroundClicked.emit()
        return super().eventFilter(obj, event)

    def add_mod(self, mod_id: str, thumbnail: QPixmap, name: str, version: str, is_favorite: bool=False, category: str="Mod", thumbnail_id: str = "", show_favorite: bool = True) -> ModCard:
        """Dynamically add a ModCard to the grid."""
        card = ModCard(
            mod_id,
            thumbnail,
            name,
            version,
            is_favorite,
            category,
            thumbnail_id=thumbnail_id,
            show_favorite=show_favorite,
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

    def _reflow(self):
        """FlowLayout auto-wraps on resize; just trigger relayout."""
        self._container.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()
