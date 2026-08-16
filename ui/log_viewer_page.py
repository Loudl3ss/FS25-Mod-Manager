from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.log_analyzer import LogAnalyzer
from ui.styles import PALETTE


class LogEntryCard(QFrame):
    def __init__(self, entry: dict[str, str], parent=None):
        super().__init__(parent)
        entry_type = entry.get("type", "INFO")
        title = entry.get("human_title", "Unknown Error")
        message = entry.get("human_msg", "")
        action = entry.get("human_action", "Inspect the log and retry.")
        raw_line = entry.get("raw_line", "")
        count = int(entry.get("count", 1) or 1)
        if count > 1:
            title = f"{title}   ×{count}"

        border_color = "#2b313b"
        title_color = PALETTE["text"]
        if entry_type == "ERROR":
            border_color = "#5c2626"
            title_color = "#e0b4b4"
        elif entry_type == "WARNING":
            border_color = "#5f4a22"
            title_color = "#e0c88e"

        self.setObjectName("LogEntryCard")
        self.setStyleSheet(
            f"""
            QFrame#LogEntryCard {{
                background-color: rgba(255, 255, 255, 0.035);
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {title_color};")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setStyleSheet(f"font-size: 12.5px; color: {PALETTE['text']};")
            msg_lbl.setWordWrap(True)
            layout.addWidget(msg_lbl)

        action_lbl = QLabel(action)
        action_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #5a9e6b;")
        action_lbl.setWordWrap(True)
        layout.addWidget(action_lbl)

        raw_lbl = QLabel(raw_line)
        raw_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        raw_lbl.setWordWrap(True)
        raw_lbl.setStyleSheet(
            f"font-family: 'Noto Sans Mono', 'Consolas', monospace; "
            f"font-size: 11px; color: {PALETTE['text_dim']};"
        )
        layout.addWidget(raw_lbl)


class LogViewerPage(QWidget):
    def __init__(self, analyzer: LogAnalyzer, parent=None):
        super().__init__(parent)
        self._analyzer = analyzer
        self._build_ui()
        self._refresh_view()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("Log Analyzer")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        top = QHBoxLayout()
        top.setSpacing(10)

        self._show_errors = QCheckBox("Show Errors")
        self._show_errors.setChecked(True)
        self._show_errors.toggled.connect(self._refresh_view)
        top.addWidget(self._show_errors)

        self._show_warnings = QCheckBox("Show Warnings")
        self._show_warnings.setChecked(True)
        self._show_warnings.toggled.connect(self._refresh_view)
        top.addWidget(self._show_warnings)

        self._show_info = QCheckBox("Show Info")
        self._show_info.setChecked(False)
        self._show_info.toggled.connect(self._refresh_view)
        top.addWidget(self._show_info)

        top.addStretch(1)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setObjectName("PrimaryBtn")
        self._refresh_btn.clicked.connect(self._refresh_view)
        top.addWidget(self._refresh_btn)

        root.addLayout(top)

        self._summary_lbl = QLabel("")
        self._summary_lbl.setObjectName("PageSubtitle")
        root.addWidget(self._summary_lbl)

        self._list = QListWidget()
        self._list.setSpacing(8)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        root.addWidget(self._list, stretch=1)

    def _is_visible_type(self, entry_type: str) -> bool:
        if entry_type == "ERROR":
            return self._show_errors.isChecked()
        if entry_type == "WARNING":
            return self._show_warnings.isChecked()
        return self._show_info.isChecked()

    def _refresh_view(self):
        self._list.clear()
        report = self._analyzer.summarize()
        errors, warnings = report["errors"], report["warnings"]
        total = report["total_lines"]

        if total == 0:
            self._summary_lbl.setText("No log file found yet — run the game once.")
        elif errors == 0 and warnings == 0:
            self._summary_lbl.setText(f"No problems found in {total} log lines.")
        else:
            self._summary_lbl.setText(
                f"{errors} error(s), {warnings} warning(s) in {total} log lines."
            )

        info_lines = [l for l in report["info_lines"] if l] if self._show_info.isChecked() else []

        for entry in report["issues"]:
            if not self._is_visible_type(entry.get("type", "INFO")):
                continue

            card = LogEntryCard(entry)
            item = QListWidgetItem()
            item.setSizeHint(card.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, card)

        if info_lines:
            # One row per line. Packing them into a single card produced a
            # widget thousands of pixels tall, which QListWidget paints only
            # partially: the text looked cut off while the scrollbar claimed
            # it had reached the end.
            header = QListWidgetItem(f"Info messages ({len(info_lines)})")
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            self._list.addItem(header)
            for line in info_lines:
                self._list.addItem(QListWidgetItem(line))

        if self._list.count() == 0:
            self._list.addItem(
                "No problems found." if report["total_lines"]
                else "No log file found yet — run the game once."
            )
