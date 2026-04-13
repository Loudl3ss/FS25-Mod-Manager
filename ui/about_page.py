"""About page."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import HSeparator
from core.version import APP_VERSION


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center container
        center = QWidget()
        center.setMaximumWidth(480)
        center.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        lay = QVBoxLayout(center)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(18)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Big logo / icon
        logo = QLabel("🚜")
        logo.setFont(QFont("", 72))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)

        name_lbl = QLabel("FS25 Manager")
        name_lbl.setObjectName("PageTitle")
        name_lbl.setFont(QFont("", 28, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name_lbl)

        ver_lbl = QLabel(f"Version {APP_VERSION}  ·  Linux Edition")
        ver_lbl.setObjectName("PageSubtitle")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ver_lbl)

        lay.addWidget(HSeparator())

        desc = QLabel(
            "FS25 Manager is an open-source desktop utility for Linux users "
            "of Farming Simulator 25.\n\n"
            "Manage local mods, browse online mod hubs, run a guided new game "
            "setup, and maintain save slots from one interface built for daily use."
        )
        desc.setObjectName("ModAuthor")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(desc)

        lay.addWidget(HSeparator())

        features = [
            ("📦", "Local Mod Manager", "Enable, disable, search and organize your installed mods"),
            ("🌐", "Online Browsing", "Browse FS25 Official, KINGMODS and FS25.NET with category filters"),
            ("🧭", "New Game Wizard", "Choose map, configure gameplay settings and build your mod loadout"),
            ("💾", "Save Manager", "Backup, restore, copy to another slot and delete save slots"),
            ("⚙️", "App Settings", "Configure game folders and refresh data without restarting the app"),
        ]

        for icon, feat_title, feat_desc in features:
            row = QHBoxLayout()
            row.setSpacing(14)

            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("", 24))
            icon_lbl.setFixedWidth(40)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(icon_lbl)

            text_col = QVBoxLayout()
            text_col.setSpacing(1)
            ft = QLabel(feat_title)
            ft.setObjectName("ModTitle")
            text_col.addWidget(ft)
            fd = QLabel(feat_desc)
            fd.setObjectName("ModMeta")
            text_col.addWidget(fd)
            row.addLayout(text_col, stretch=1)

            lay.addLayout(row)

        lay.addWidget(HSeparator())

        footer = QLabel("Built with Python & PyQt6  ·  MIT License")
        footer.setObjectName("PageSubtitle")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(footer)

        lay.addStretch()

        root.addStretch()
        root.addWidget(center, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch()
