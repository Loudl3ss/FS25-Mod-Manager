"""FS25 Manager – Entry Point."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QLockFile, QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QInputDialog, QMessageBox, QProgressDialog,
)

from core.fs25_detector import FS25Detector
from ui.main_window import MainWindow
from ui.styles import DARK_THEME

# Held for the process lifetime; released when the process exits.
# New filename on purpose: the pre-1.2 lock file held a bare PID, which
# QLockFile cannot parse and would wait out as stale.
_lock = QLockFile("/tmp/fs25-mod-manager.lock")


def browse_for_path() -> str | None:
    """Let the user pick the FS25 data folder by hand."""
    folder = QFileDialog.getExistingDirectory(
        None,
        "Select FS25 User Data Folder",
        str(Path.home()),
    )
    return folder or None


def auto_detect_path() -> list[str]:
    """Scan for FS25 installs behind a progress dialog. Returns what it found."""
    dialog = QProgressDialog("Looking for Farming Simulator 25…", "Cancel", 0, 1)
    dialog.setWindowTitle("FS25 Manager – Searching")
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setValue(0)

    def on_progress(done: int, total: int, path: str) -> bool:
        dialog.setMaximum(total)
        dialog.setValue(done)
        dialog.setLabelText(f"Looking for Farming Simulator 25…\n\n{path}")
        # ponytail: scan runs on the GUI thread; it is a few hundred stat()
        # calls. Move to a QThread if it ever blocks noticeably.
        QApplication.processEvents()
        return not dialog.wasCanceled()

    try:
        return FS25Detector.search(progress=on_progress)
    finally:
        dialog.close()


def confirm_path(found: list[str]) -> str | None:
    """Ask the user to confirm a detected path, or fall back to browsing."""
    if not found:
        install = FS25Detector.find_game_install()
        msg = QMessageBox()
        msg.setWindowTitle("FS25 Manager – Setup")
        msg.setIcon(QMessageBox.Icon.Question)
        if install:
            msg.setText("Farming Simulator 25 is installed, but has no user data yet.")
            msg.setInformativeText(
                f"Game found at:\n{install}\n\n"
                "Start the game once so it creates its mods and savegame folders, "
                "then reopen FS25 Manager. You can also select the folder yourself."
            )
        else:
            msg.setText(
                "Farming Simulator 25 data folder not found automatically.\n\n"
                "Please select your FS25 user data directory manually.\n"
                "(It usually contains 'mods' and 'savegame1' folders.)"
            )
        msg.setStandardButtons(
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel
        )
        msg.button(QMessageBox.StandardButton.Open).setText("Browse…")
        if msg.exec() == QMessageBox.StandardButton.Cancel:
            return None
        return browse_for_path()

    if len(found) > 1:
        choice, ok = QInputDialog.getItem(
            None,
            "FS25 Manager – Setup",
            "Several Farming Simulator 25 folders were found.\nWhich one should be used?",
            found,
            0,
            False,
        )
        return choice if ok else None

    msg = QMessageBox()
    msg.setWindowTitle("FS25 Manager – Setup")
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setText("Found Farming Simulator 25 here:")
    msg.setInformativeText(found[0])
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Open
    )
    msg.button(QMessageBox.StandardButton.Yes).setText("Use this folder")
    msg.button(QMessageBox.StandardButton.Open).setText("Choose another…")
    msg.setDefaultButton(QMessageBox.StandardButton.Yes)

    if msg.exec() == QMessageBox.StandardButton.Yes:
        return found[0]
    return browse_for_path()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FS25 Manager")
    app.setOrganizationName("FS25Tools")

    if not _lock.tryLock(0):
        QMessageBox.information(
            None,
            "FS25 Manager",
            "FS25 Manager is already running.",
        )
        sys.exit(0)

    # Apply global dark theme
    app.setStyleSheet(DARK_THEME)

    # Set default font
    font = QFont("Ubuntu", 11)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(font)

    settings = QSettings()

    # 1. Try to load last saved path
    data_path = settings.value("last_data_path", "")

    # 2. Scan for installs, then let the user confirm what was found
    if not data_path or not FS25Detector.validate_path(data_path):
        data_path = confirm_path(auto_detect_path())
        if not data_path:
            sys.exit(0)

        if not FS25Detector.validate_path(data_path):
            QMessageBox.warning(
                None,
                "Invalid Folder",
                "The selected folder does not appear to be a valid "
                "Farming Simulator 25 data directory.\n\n"
                "The app will load anyway — some features may be unavailable.",
            )
            
    # Always save the working path for next time
    if data_path:
        settings.setValue("last_data_path", data_path)

    window = MainWindow(data_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
