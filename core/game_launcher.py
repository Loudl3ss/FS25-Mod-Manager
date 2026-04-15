"""Game launch helpers."""
from __future__ import annotations

import subprocess


class GameLauncher:
    """Utility methods for launching Farming Simulator via Steam."""

    FS25_APP_ID = "2300320"

    @classmethod
    def launch_steam_game(cls) -> tuple[bool, str]:
        """Launch FS25 through Steam using available Linux strategies."""
        try:
            subprocess.Popen(
                ["steam", "-applaunch", cls.FS25_APP_ID],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True, "Game launch started (Steam CLI)..."
        except FileNotFoundError:
            pass

        try:
            subprocess.Popen(
                ["distrobox-host-exec", "steam", "-applaunch", cls.FS25_APP_ID],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True, "Game launch started (Distrobox Host)..."
        except FileNotFoundError:
            pass

        try:
            subprocess.Popen(
                ["flatpak", "run", "com.valvesoftware.Steam", "-applaunch", cls.FS25_APP_ID],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True, "Game launch started (Flatpak)..."
        except Exception as exc:
            return False, f"Failed to launch game: {exc}"
