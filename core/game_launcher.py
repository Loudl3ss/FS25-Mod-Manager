"""Game launch helpers."""
from __future__ import annotations

import subprocess
from typing import Sequence


class GameLauncher:
    """Utility methods for launching Farming Simulator via Steam."""

    FS25_APP_ID = "2300320"

    @classmethod
    def _launch_strategies(cls) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Ordered command strategies for Linux desktop environments."""
        return (
            ("Steam CLI", ("steam", "-applaunch", cls.FS25_APP_ID)),
            (
                "Distrobox Host",
                ("distrobox-host-exec", "steam", "-applaunch", cls.FS25_APP_ID),
            ),
            (
                "Flatpak",
                ("flatpak", "run", "com.valvesoftware.Steam", "-applaunch", cls.FS25_APP_ID),
            ),
        )

    @staticmethod
    def _launch_command(command: Sequence[str]) -> None:
        subprocess.Popen(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @classmethod
    def launch_steam_game(cls) -> tuple[bool, str]:
        """Launch FS25 through Steam using available Linux strategies."""
        for strategy_name, command in cls._launch_strategies():
            try:
                cls._launch_command(command)
                return True, f"Game launch started ({strategy_name})..."
            except FileNotFoundError:
                continue
            except Exception as exc:
                return False, f"Failed to launch game via {strategy_name}: {exc}"

        return False, "Failed to launch game: no supported Steam command found"
