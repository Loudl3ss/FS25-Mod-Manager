"""Tests for game launcher strategy fallback behavior."""

import unittest
from unittest.mock import patch

from core.game_launcher import GameLauncher


class TestGameLauncher(unittest.TestCase):
    def test_first_strategy_success(self) -> None:
        with patch("core.game_launcher.subprocess.Popen") as popen:
            ok, message = GameLauncher.launch_steam_game()

        self.assertTrue(ok)
        self.assertIn("Steam CLI", message)
        popen.assert_called_once()

    def test_fallback_to_second_strategy(self) -> None:
        side_effects = [FileNotFoundError("steam missing"), object()]

        with patch("core.game_launcher.subprocess.Popen", side_effect=side_effects) as popen:
            ok, message = GameLauncher.launch_steam_game()

        self.assertTrue(ok)
        self.assertIn("Distrobox Host", message)
        self.assertEqual(popen.call_count, 2)

    def test_all_strategies_missing_returns_clear_error(self) -> None:
        side_effects = [
            FileNotFoundError("steam missing"),
            FileNotFoundError("distrobox missing"),
            FileNotFoundError("flatpak missing"),
        ]

        with patch("core.game_launcher.subprocess.Popen", side_effect=side_effects):
            ok, message = GameLauncher.launch_steam_game()

        self.assertFalse(ok)
        self.assertIn("no supported Steam command", message)

    def test_non_not_found_error_aborts_current_strategy(self) -> None:
        with patch("core.game_launcher.subprocess.Popen", side_effect=PermissionError("boom")):
            ok, message = GameLauncher.launch_steam_game()

        self.assertFalse(ok)
        self.assertIn("Steam CLI", message)
        self.assertIn("boom", message)


if __name__ == "__main__":
    unittest.main()