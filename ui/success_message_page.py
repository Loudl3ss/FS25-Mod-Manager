"""Success message page for New Game wizard."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class SuccessMessageView(QWidget):
    """Step 4: Success message after game creation."""

    wizard_completed = pyqtSignal()  # Emitted when user acknowledges success

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(40, 40, 40, 20)

        title = QLabel("✅  Game Created Successfully!")
        title.setObjectName("PageTitle")
        header_lay.addWidget(title)

        info = QLabel("Your new farming career is ready to begin.")
        info.setObjectName("PageSubtitle")
        header_lay.addWidget(info)

        layout.addWidget(header)

        # Content area
        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(40, 20, 40, 20)

        success_msg = QLabel("The game save has been created with your selected map, settings, and mods.\n\nYou can now launch Farming Simulator 25 and start playing!")
        success_msg.setStyleSheet("color: #e2e8f0; font-size: 14px; line-height: 1.5;")
        success_msg.setWordWrap(True)
        content_lay.addWidget(success_msg)

        content_lay.addStretch()
        layout.addWidget(content)

        # Navigation buttons
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b;")
        nav_lay = QHBoxLayout(nav_bar)
        nav_lay.setContentsMargins(40, 16, 40, 16)

        nav_lay.addStretch()

        self.btn_finish = QPushButton("Finish")
        self.btn_finish.setObjectName("PrimaryBtn")
        self.btn_finish.clicked.connect(self.wizard_completed.emit)
        nav_lay.addWidget(self.btn_finish)

        layout.addWidget(nav_bar)