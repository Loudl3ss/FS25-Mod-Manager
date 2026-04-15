"""Reusable widgets for FS25 Manager."""
from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve, QVariantAnimation, QRect, Qt, QSize, QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PyQt6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QStyle, QSizePolicy, QVBoxLayout, QWidget,
)

from core.thumbnail_loader import ThumbnailLoader
from ui.style_helpers import refresh_widget_style, set_bool_property


# ─────────────────────────────────────────────────────────────────────────────
# SidebarNavButton
# ─────────────────────────────────────────────────────────────────────────────
class SidebarNavButton(QPushButton):
    """Sidebar navigation button with optional text icon fallback."""

    def __init__(self, text: str, generic_icon_text: str = "", parent=None):
        super().__init__(text, parent)
        self._generic_icon_text = generic_icon_text
        self._badge_count = 0
        self._badge_visible = False
        self.setObjectName("NavBtn")
        self.setCheckable(True)

    def set_badge_count(self, count: int, show: bool = True):
        self._badge_count = max(0, int(count))
        self._badge_visible = show
        self.update()

    def paintEvent(self, a0):
        super().paintEvent(a0)
        if not self._badge_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        count_txt = str(self._badge_count)
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(count_txt)
        badge_w = max(18, text_w + 10)
        badge_h = 18
        badge_x = self.width() - badge_w - 50
        badge_y = (self.height() - badge_h) // 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#16a34a"))
        painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 9, 9)

        painter.setPen(QColor("#ecfdf5"))
        painter.drawText(
            QRect(badge_x, badge_y, badge_w, badge_h),
            Qt.AlignmentFlag.AlignCenter,
            count_txt,
        )


# ─────────────────────────────────────────────────────────────────────────────
# ToggleSwitch
# ─────────────────────────────────────────────────────────────────────────────
class ToggleSwitch(QWidget):
    """Animated iOS-style toggle switch."""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked: bool = True):
        super().__init__(parent)
        self._checked = checked
        self._thumb_x: float = 22.0 if checked else 2.0
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.valueChanged.connect(self._on_thumb_animation_value)

    def _on_thumb_animation_value(self, value):
        self._thumb_x = float(value)
        self.update()

    # ── state ─────────────────────────────────────────────────────────────────
    @property
    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool, emit: bool = False):
        if self._checked == checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setStartValue(float(self._thumb_x))
        self._anim.setEndValue(22.0 if checked else 2.0)
        self._anim.start()
        if emit:
            self.toggled.emit(checked)

    # ── events ────────────────────────────────────────────────────────────────
    def mousePressEvent(self, a0):
        self.set_checked(not self._checked, emit=True)
        super().mousePressEvent(a0)

    def paintEvent(self, a0):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # track
        track_color = QColor("#16a34a") if self._checked else QColor("#334155")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, h // 2, h // 2)
        p.drawPath(path)

        # thumb
        p.setBrush(QColor("#ffffff"))
        thumb_r = 10
        p.drawEllipse(
            int(self._thumb_x) + 1, h // 2 - thumb_r,
            thumb_r * 2, thumb_r * 2,
        )
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# StatCard
# ─────────────────────────────────────────────────────────────────────────────
class StatCard(QFrame):
    """A minimal stat card for the header."""

    def __init__(self, title: str, value: str, icon_str: str, object_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_id)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(96)

        lay = QGridLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        
        # Icon at Top Right
        icon_lbl = QLabel(icon_str)
        icon_lbl.setObjectName("StatIcon")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        lay.addWidget(icon_lbl, 0, 1)

        # Value at Top Left
        self._val_lbl = QLabel(value)
        self._val_lbl.setObjectName("StatValue")
        self._val_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lay.addWidget(self._val_lbl, 0, 0)

        # Category at Bottom Left
        cat_lbl = QLabel(title.upper())
        cat_lbl.setObjectName("StatCategory")
        cat_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        lay.addWidget(cat_lbl, 1, 0, 1, 2)
        
        # shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)

    def set_value(self, v: str):
        self._val_lbl.setText(v)


# ─────────────────────────────────────────────────────────────────────────────
# Badge
# ─────────────────────────────────────────────────────────────────────────────
class Badge(QLabel):
    """A colored pill badge."""

    def __init__(self, text: str, kind: str = "enabled", parent=None):
        super().__init__(text.upper(), parent)
        self.set_kind(kind)

    def set_kind(self, kind: str):
        if kind == "enabled":
            self.setObjectName("BadgeEnabled")
        else:
            self.setObjectName("BadgeDisabled")
        self.setFixedHeight(18)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        refresh_widget_style(self)


# ─────────────────────────────────────────────────────────────────────────────
# ClickableFrame (base for cards)
# ─────────────────────────────────────────────────────────────────────────────
class ClickableFrame(QFrame):
    """QFrame that emits a clicked signal."""

    clicked = pyqtSignal()

    def mousePressEvent(self, a0):
        self.clicked.emit()
        super().mousePressEvent(a0)


# ─────────────────────────────────────────────────────────────────────────────
# ModCard
# ─────────────────────────────────────────────────────────────────────────────
class ModCard(ClickableFrame):
    """Card widget displayed in the mod list."""

    delete_requested = pyqtSignal(object)       # emits ModInfo
    favorite_toggled = pyqtSignal(object, bool) # emits (ModInfo, is_favorite)

    def __init__(self, mod_info, is_favorite: bool = False, parent=None):
        super().__init__(parent)
        self.mod_info = mod_info
        self.setObjectName("ModCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        CARD_WIDTH = 180
        CARD_HEIGHT = 180
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        
        self.setStyleSheet("""
            QFrame#ModCard {
                background: #1e293b;
                border: 2px solid #22c55e;
                border-radius: 12px;
            }
            QFrame#ModCard[selected="true"] {
                border: 2px solid #fbbf24;
                background: #334155;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── thumbnail ────────────────────────────────────────────────────────────
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(CARD_WIDTH - 4, 134)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._icon_lbl.setStyleSheet(
            "border-top-left-radius: 10px; border-top-right-radius: 10px; "
            "border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; "
            "background:#0f172a; font-size: 64px; border: none;"
        )
        pix = ThumbnailLoader.obtain_local_pixmap(
            mod_info.icon_data,
            mod_id=getattr(mod_info, "id", ""),
            thumbnail_id=getattr(mod_info, "thumbnail_id", ""),
        )
        if not pix.isNull():
            self._icon_lbl.setPixmap(
                pix.scaled(CARD_WIDTH - 4, 134, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self._icon_lbl.setText("🌾")

        outer.addWidget(self._icon_lbl)

        # Favourite star button - absolutely positioned in top right
        self._is_favorite = is_favorite
        self._star_btn = QPushButton("★" if is_favorite else "☆", self)
        self._star_btn.setObjectName("StarBtn")
        set_bool_property(self._star_btn, "active", is_favorite)
        self._star_btn.setFixedSize(32, 32)
        font = self._star_btn.font()
        font.setPointSize(20)
        self._star_btn.setFont(font)
        self._star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._star_btn.setToolTip("Add to Favorites" if not is_favorite else "Remove from Favorites")
        self._star_btn.clicked.connect(self._on_star_clicked)
        self._star_btn.move(CARD_WIDTH - 32 - 4, 4)
        self._star_btn.raise_()

        # ── bottom text block ────────────────────────────────────────────────
        text_lay = QVBoxLayout()
        text_lay.setContentsMargins(10, 0, 10, 6)
        text_lay.setSpacing(0)
        
        text_lay.addStretch()

        # Use QFontMetrics to elide the text perfectly
        full_title = mod_info.title or mod_info.name
        font_title = QFont()
        font_title.setPointSize(9)
        metrics = QFontMetrics(font_title)
        elided_title = metrics.elidedText(full_title, Qt.TextElideMode.ElideRight, CARD_WIDTH - 24)

        self._title_lbl = QLabel(elided_title)
        self._title_lbl.setObjectName("ModTitle")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self._title_lbl.setWordWrap(False)
        self._title_lbl.setFixedHeight(16)
        self._title_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        self._title_lbl.setFont(font_title)
        text_lay.addWidget(self._title_lbl)

        v_str = f"v{mod_info.version}" if mod_info.version else "v1.0"
        self._meta_lbl = QLabel(v_str)
        self._meta_lbl.setObjectName("ModMeta")
        font_meta = QFont()
        font_meta.setPointSize(8)
        self._meta_lbl.setFont(font_meta)
        self._meta_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self._meta_lbl.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
        self._meta_lbl.setFixedHeight(16)
        text_lay.addWidget(self._meta_lbl)
        
        outer.addLayout(text_lay)

    def _on_star_clicked(self):
        self._is_favorite = not self._is_favorite
        self._star_btn.setText("★" if self._is_favorite else "☆")
        set_bool_property(self._star_btn, "active", self._is_favorite)
        self._star_btn.setToolTip(
            "Remove from Favorites" if self._is_favorite else "Add to Favorites"
        )
        self.favorite_toggled.emit(self.mod_info, self._is_favorite)

    def set_favorite(self, is_fav: bool):
        self._is_favorite = is_fav
        self._star_btn.setText("★" if is_fav else "☆")
        set_bool_property(self._star_btn, "active", is_fav)

    def set_selected(self, selected: bool):
        set_bool_property(self, "selected", selected)


# ─────────────────────────────────────────────────────────────────────────────
# SaveCard
# ─────────────────────────────────────────────────────────────────────────────
class SaveCard(ClickableFrame):
    """Card displaying a save game slot."""

    backup_requested = pyqtSignal(object)   # emits SaveInfo
    restore_requested = pyqtSignal(object)  # emits SaveInfo
    delete_requested = pyqtSignal(object)   # emits SaveInfo
    copy_requested = pyqtSignal(object)     # emits SaveInfo

    def __init__(self, save_info, parent=None):
        super().__init__(parent)
        self.save_info = save_info
        self.setObjectName("ModCard")  # reuse card styling
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(110)

        main = QHBoxLayout(self)
        main.setContentsMargins(14, 12, 14, 12)
        main.setSpacing(14)

        # ── Slot number circle ───────────────────────────────────────────────
        slot_lbl = QLabel(str(save_info.slot))
        slot_lbl.setFixedSize(46, 46)
        slot_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slot_font = QFont("", 18, QFont.Weight.Bold)
        slot_lbl.setFont(slot_font)
        slot_lbl.setStyleSheet(
            "border-radius: 23px; background: #14532d; color: #4ade80;"
            if save_info.exists else
            "border-radius: 23px; background: #1e293b; color: #64748b;"
        )
        main.addWidget(slot_lbl)

        # ── Column 2: info block ─────────────────────────────────────────────
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        info_col.setContentsMargins(0, 0, 0, 0)

        if save_info.exists:
            farm = QLabel(save_info.farm_name or f"Save {save_info.slot}")
            farm.setObjectName("ModTitle")
            info_col.addWidget(farm)

            map_lbl = QLabel(save_info.map_title or "Unknown Map")
            map_lbl.setObjectName("ModAuthor")
            info_col.addWidget(map_lbl)

            money_str = f"${save_info.money:,.0f}" if save_info.money else ""
            time_h = int(save_info.play_time)
            time_str = f"⏱ {time_h}h" if time_h else ""
            date_str = save_info.save_date or ""
            detail_parts = [x for x in [money_str, time_str, date_str] if x]
            detail_lbl = QLabel("   ".join(detail_parts))
            detail_lbl.setObjectName("ModMeta")
            info_col.addWidget(detail_lbl)
        else:
            empty_lbl = QLabel(f"Slot {save_info.slot} — Empty")
            empty_lbl.setObjectName("ModMeta")
            info_col.addWidget(empty_lbl)

        main.addLayout(info_col, stretch=1)

        # ── Column 3: buttons ────────────────────────────────────────────────
        if save_info.exists:
            from PyQt6.QtWidgets import QPushButton
            btn_col = QVBoxLayout()
            btn_col.setContentsMargins(0, 0, 0, 0)
            btn_col.setSpacing(0)
            btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(0, 0, 0, 0)
            btn_row.setSpacing(12)
            btn_row.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            bak_btn = QPushButton("Backup")
            bak_btn.setObjectName("ToolBtn")
            bak_btn.setFixedSize(100, 40)
            bak_btn.clicked.connect(lambda: self.backup_requested.emit(self.save_info))
            btn_row.addWidget(bak_btn)

            cpy_btn = QPushButton("Copy to")
            cpy_btn.setObjectName("ToolBtn")
            cpy_btn.setFixedSize(100, 40)
            cpy_btn.clicked.connect(lambda: self.copy_requested.emit(self.save_info))
            btn_row.addWidget(cpy_btn)

            res_btn = QPushButton("Restore")
            res_btn.setObjectName("SuccessBtn")
            res_btn.setFixedSize(100, 40)
            res_btn.clicked.connect(lambda: self.restore_requested.emit(self.save_info))
            btn_row.addWidget(res_btn)

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("DangerBtn")
            del_btn.setFixedSize(100, 40)
            del_btn.clicked.connect(lambda: self.delete_requested.emit(self.save_info))
            btn_row.addWidget(del_btn)

            btn_col.addLayout(btn_row)
            main.addLayout(btn_col)


# ─────────────────────────────────────────────────────────────────────────────
# HSeparator
# ─────────────────────────────────────────────────────────────────────────────
class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._expanded = False

        self._header = QPushButton(title)
        self._header.setObjectName("CollapsibleHeader")
        self._header.setCheckable(True)
        self._header.setChecked(self._expanded)
        style = self._header.style() or QApplication.style()
        if style is not None:
            self._header.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
        self._header.setIconSize(QSize(14, 14))
        self._header.clicked.connect(self._on_header_clicked)

        self._content = QWidget()
        self._content.setVisible(self._expanded)
        self._content.setObjectName("CollapsibleContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self._header)
        layout.addWidget(self._content)

        self._update_arrow()

    def _on_header_clicked(self, checked: bool):
        self._expanded = checked
        self._content.setVisible(self._expanded)
        self._update_arrow()

    def _update_arrow(self):
        style = self._header.style() or QApplication.style()
        if style is None:
            return
        base_icon = style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        pixmap = base_icon.pixmap(self._header.iconSize())
        angle = 90 if self._expanded else 0
        rotated = pixmap.transformed(QTransform().rotate(angle), Qt.TransformationMode.SmoothTransformation)
        self._header.setIcon(QIcon(rotated))
        self._header.setProperty("expanded", self._expanded)
        refresh_widget_style(self._header)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout


class HSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HSep")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)

class PathSettingRow(QFrame):
    """Reusable row for folder/path settings with browse action."""

    browse_requested = pyqtSignal()

    def __init__(self, current_path: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "PathSettingRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.path_label = QLabel(current_path if current_path else "No path selected")
        self.path_label.setObjectName("PathLabel")
        self.path_label.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("ToolBtn")
        browse_btn.setFixedSize(100, 36)
        browse_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_btn.clicked.connect(self.browse_requested.emit)
        layout.addWidget(browse_btn)

    def set_path(self, path: str) -> None:
        self.path_label.setText(path if path else "No path selected")
