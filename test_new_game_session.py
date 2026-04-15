"""Unit tests for NewGameSession state behavior."""

from __future__ import annotations

import unittest

from core.new_game_session import NewGameSession


class TestNewGameSession(unittest.TestCase):
    def test_initial_state_is_empty(self) -> None:
        session = NewGameSession()

        self.assertIsNone(session.selected_map)
        self.assertEqual(session.settings, {})
        self.assertEqual(session.selected_mods, [])

    def test_reset_clears_all_state(self) -> None:
        session = NewGameSession(
            selected_map="sample-map",
            settings={"economicDifficulty": 3},
            selected_mods=["mod_a", "mod_b"],
        )

        session.reset()

        self.assertIsNone(session.selected_map)
        self.assertEqual(session.settings, {})
        self.assertEqual(session.selected_mods, [])


if __name__ == "__main__":
    unittest.main()
