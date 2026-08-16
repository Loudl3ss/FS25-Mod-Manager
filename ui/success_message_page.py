"""Custom success dialog for New Game wizard."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.game_launcher import GameLauncher


class GameCreatedDialog(QDialog):
    """Card-style success dialog shown after a new game save is created."""

    def __init__(self, save_name: str, slot: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self._result_action = "hub"
        self._build_ui(save_name, slot)
        self.adjustSize()

    def _build_ui(self, save_name: str, slot: int):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("GameCreatedCard")
        card.setFixedWidth(560)
        card.setStyleSheet("""
            QWidget#GameCreatedCard {
                background-color: #161a21;
                border-radius: 16px;
                border: 1px solid #2b313b;
            }
            QLabel {
                background: transparent;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 36, 36, 32)
        layout.setSpacing(0)

        # 🎉 Emoji
        emoji_lbl = QLabel("🎉")
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setStyleSheet("font-size: 52px;")
        layout.addWidget(emoji_lbl)
        layout.addSpacing(16)

        # Title
        title_lbl = QLabel("Save Game Created!")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #e6eaf0; font-size: 22px; font-weight: 700;")
        layout.addWidget(title_lbl)
        layout.addSpacing(10)

        # Subtitle — green
        sub_lbl = QLabel(f'"{save_name}" has been created.')
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("color: #5a9e6b; font-size: 15px; font-weight: 500;")
        sub_lbl.setWordWrap(True)
        layout.addWidget(sub_lbl)
        layout.addSpacing(10)

        # Body — gray
        body_lbl = QLabel(
            f"Load it from Career \u2192 Save Game {slot}\n"
            "in Farming Simulator 25."
        )
        body_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_lbl.setStyleSheet("color: #8b94a1; font-size: 13px;")
        body_lbl.setWordWrap(True)
        layout.addWidget(body_lbl)
        layout.addSpacing(32)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_another = QPushButton("Create Another")
        btn_another.setFixedHeight(44)
        btn_another.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_another.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_another.setStyleSheet("""
            QPushButton {
                background-color: #2b313b;
                color: #d5dbe3;
                border: 1px solid #414b59;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #2b313b;
                border-color: #7d8694;
            }
        """)
        btn_another.clicked.connect(self._on_another)

        btn_launch = QPushButton("Launch Game")
        btn_launch.setObjectName("LaunchBtn")
        btn_launch.setFixedHeight(44)
        btn_launch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_launch.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #4a8c5c;
                color: #0b0e12;
                border: 1px solid #4a8c5c;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #3f7a4f;
                border-color: #3f7a4f;
            }
            QPushButton:pressed {
                background-color: #356a45;
                border-color: #356a45;
            }
        """)
        btn_launch.clicked.connect(self._on_launch_game)

        btn_hub = QPushButton("Back to Hub")
        btn_hub.setFixedHeight(44)
        btn_hub.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_hub.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_hub.setStyleSheet("""
            QPushButton {
                background-color: #3f7d51;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #356a45;
            }
        """)
        btn_hub.clicked.connect(self._on_hub)

        btn_row.addWidget(btn_another)
        btn_row.addWidget(btn_launch)
        btn_row.addWidget(btn_hub)
        btn_row.setStretch(0, 1)
        btn_row.setStretch(1, 1)
        btn_row.setStretch(2, 1)
        layout.addLayout(btn_row)

        root.addWidget(card)

    def _on_another(self):
        self._result_action = "another"
        self.accept()

    def _on_hub(self):
        self._result_action = "hub"
        self.accept()

    def _on_launch_game(self):
        ok, message = GameLauncher.launch_steam_game()
        if not ok:
            QMessageBox.warning(self, "Launch Failed", message)
            return
        self._result_action = "hub"
        self.accept()

    def result_action(self) -> str:
        """Returns 'another' or 'hub' based on which button was pressed."""
        return self._result_action
