"""Reusable widgets for FS25 Manager."""
from __future__ import annotations

from PyQt6.QtCore import QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout,
)

from ui.style_helpers import apply_card_shadow, refresh_widget_style


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
        # Take whatever width the sidebar gives instead of forcing the sidebar
        # wider than its own fixed width, which caused sideways scrolling.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

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
        painter.setBrush(QColor("#3f7d51"))
        painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 9, 9)

        painter.setPen(QColor("#d5dbe3"))
        painter.drawText(
            QRect(badge_x, badge_y, badge_w, badge_h),
            Qt.AlignmentFlag.AlignCenter,
            count_txt,
        )


# ─────────────────────────────────────────────────────────────────────────────
# StatCard
# ─────────────────────────────────────────────────────────────────────────────
class StatCard(QFrame):
    """A minimal stat card for the header."""

    def __init__(self, title: str, value: str, icon_str: str, object_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_id)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(74)

        lay = QGridLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        
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
        cat_lbl = QLabel(title)
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
        super().__init__(text, parent)
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
# SaveCard
# ─────────────────────────────────────────────────────────────────────────────
class SaveCard(ClickableFrame):
    """Card displaying a save game slot."""

    backup_requested = pyqtSignal(object)   # emits SaveInfo
    restore_requested = pyqtSignal(object)  # emits SaveInfo
    delete_requested = pyqtSignal(object)   # emits SaveInfo
    copy_requested = pyqtSignal(object)     # emits SaveInfo
    selection_changed = pyqtSignal()

    def __init__(self, save_info, parent=None):
        super().__init__(parent)
        self.save_info = save_info
        self.setObjectName("SaveRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(64)

        main = QHBoxLayout(self)
        main.setContentsMargins(12, 6, 12, 6)
        main.setSpacing(12)

        # Only populated slots can take part in bulk actions. Track this with
        # an explicit flag: isVisible() is False until the page is shown.
        self._selectable = bool(save_info.exists)
        self._check = QCheckBox()
        self._check.setVisible(self._selectable)
        self._check.toggled.connect(lambda _: self.selection_changed.emit())
        main.addWidget(self._check, alignment=Qt.AlignmentFlag.AlignVCenter)

        # ── Slot number circle ───────────────────────────────────────────────
        slot_lbl = QLabel(str(save_info.slot))
        slot_lbl.setFixedSize(32, 32)
        slot_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slot_font = QFont("", 13, QFont.Weight.Bold)
        slot_lbl.setFont(slot_font)
        slot_lbl.setStyleSheet(
            "border-radius: 16px; background: rgba(90, 158, 107, 0.18); color: #7cb98d;"
            if save_info.exists else
            "border-radius: 16px; background: rgba(255, 255, 255, 0.05); color: #7d8694;"
        )
        main.addWidget(slot_lbl)

        # ── Column 2: info block ─────────────────────────────────────────────
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        info_col.setContentsMargins(0, 0, 0, 0)

        if save_info.exists:
            farm = QLabel(save_info.farm_name or f"Save {save_info.slot}")
            farm.setObjectName("ModTitle")
            info_col.addWidget(farm)

            # One meta line instead of three, so the row stays compact.
            money_str = f"${save_info.money:,.0f}" if save_info.money else ""
            time_h = int(save_info.play_time)
            time_str = f"{time_h}h" if time_h else ""
            parts = [x for x in [save_info.map_title or "Unknown Map", money_str,
                                 time_str, save_info.save_date or ""] if x]
            detail_lbl = QLabel("  ·  ".join(parts))
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
            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(0, 0, 0, 0)
            btn_row.setSpacing(6)
            btn_row.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            bak_btn = QPushButton("Backup")
            bak_btn.setObjectName("ToolBtn")
            bak_btn.setFixedSize(78, 28)
            bak_btn.clicked.connect(lambda: self.backup_requested.emit(self.save_info))
            btn_row.addWidget(bak_btn)

            cpy_btn = QPushButton("Copy to")
            cpy_btn.setObjectName("ToolBtn")
            cpy_btn.setFixedSize(78, 28)
            cpy_btn.clicked.connect(lambda: self.copy_requested.emit(self.save_info))
            btn_row.addWidget(cpy_btn)

            res_btn = QPushButton("Restore")
            res_btn.setObjectName("SuccessBtn")
            res_btn.setFixedSize(78, 28)
            res_btn.clicked.connect(lambda: self.restore_requested.emit(self.save_info))
            btn_row.addWidget(res_btn)

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("DangerBtn")
            del_btn.setFixedSize(78, 28)
            del_btn.clicked.connect(lambda: self.delete_requested.emit(self.save_info))
            btn_row.addWidget(del_btn)

            main.addLayout(btn_row)

    def is_checked(self) -> bool:
        return self._selectable and self._check.isChecked()

    def set_checked(self, checked: bool) -> None:
        if self._selectable:
            self._check.setChecked(checked)


# ─────────────────────────────────────────────────────────────────────────────
# HSeparator
# ─────────────────────────────────────────────────────────────────────────────
class HSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HSep")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)

class PathSettingRow(QFrame):
    """Reusable row for folder/path settings with browse action."""

    browse_requested = pyqtSignal()
    scan_requested = pyqtSignal()

    def __init__(self, current_path: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "PathSettingRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.path_label = QLabel(current_path if current_path else "No path selected")
        self.path_label.setObjectName("PathLabel")
        self.path_label.setStyleSheet("color: #c2c9d3; font-size: 12px;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label, stretch=1)

        scan_btn = QPushButton("Scan")
        scan_btn.setObjectName("ToolBtn")
        scan_btn.setFixedHeight(30)
        scan_btn.setToolTip("Detect this folder automatically")
        scan_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        scan_btn.clicked.connect(self.scan_requested.emit)
        layout.addWidget(scan_btn)

        browse_btn = QPushButton("Browse...")
        browse_btn.setObjectName("ToolBtn")
        browse_btn.setFixedHeight(30)
        browse_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse_btn.clicked.connect(self.browse_requested.emit)
        layout.addWidget(browse_btn)

    def set_path(self, path: str) -> None:
        self.path_label.setText(path if path else "No path selected")
