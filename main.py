"""FS25 Manager – Entry Point."""
from __future__ import annotations

import sys
import os
import signal
import time

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from core.fs25_detector import FS25Detector
from ui.main_window import MainWindow
from ui.styles import DARK_THEME

LOCK_FILE = "/tmp/mod_manager.lock"

def enforce_single_instance():
    """Ensure only one instance is running, killing the previous one via lock file."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            
            # Check if process is running
            os.kill(old_pid, 0)
            
            # Process exists, let's terminate it
            os.kill(old_pid, signal.SIGTERM)
            
            # Wait up to 1 second
            for _ in range(10):
                time.sleep(0.1)
                try:
                    os.kill(old_pid, 0)
                except OSError:
                    break
            else:
                # Still running, force kill
                os.kill(old_pid, signal.SIGKILL)
                
        except (ValueError, OSError):
            # PID not running, or permission denied, or invalid pid
            pass
            
    # Write current PID to lock file
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
    except IOError:
        pass


def choose_path(app: QApplication) -> str | None:
    """Show a dialog to let the user manually pick the FS25 data folder."""
    msg = QMessageBox()
    msg.setWindowTitle("FS25 Manager – Setup")
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setText(
        "Farming Simulator 25 data folder not found automatically.\n\n"
        "Please select your FS25 user data directory manually.\n"
        "(It usually contains 'mods' and 'savegame1' folders.)"
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel
    )
    msg.button(QMessageBox.StandardButton.Open).setText("Browse…")
    result = msg.exec()

    if result == QMessageBox.StandardButton.Cancel:
        return None

    folder = QFileDialog.getExistingDirectory(
        None,
        "Select FS25 User Data Folder",
        str(user_home()),
    )
    return folder or None


def user_home() -> "Path":
    from pathlib import Path
    return Path.home()


def main():
    enforce_single_instance()
    
    app = QApplication(sys.argv)
    app.setApplicationName("FS25 Manager")
    app.setOrganizationName("FS25Tools")

    # Apply global dark theme
    app.setStyleSheet(DARK_THEME)

    # Set default font
    font = QFont("Ubuntu", 11)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(font)

    settings = QSettings()
    
    # 1. Try to load last saved path
    data_path = settings.value("last_data_path", "")

    # 2. Try to auto-detect FS25 path if saved path is invalid or empty
    if not data_path or not FS25Detector.validate_path(data_path):
        data_path = FS25Detector.find_user_data_path()

    # 3. Prompt user if both failed
    if not data_path or not FS25Detector.validate_path(data_path):
        data_path = choose_path(app)
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
