"""Tests for shared UI helper modules introduced during refactors."""

import unittest

from ui.layout_helpers import save_slot_grid_position
from ui.network_helpers import build_retry_session


class TestLayoutHelpers(unittest.TestCase):
    def test_save_slot_grid_position_defaults(self) -> None:
        """Slots should fill rows first and then move to next column."""
        self.assertEqual(save_slot_grid_position(1), (0, 0))
        self.assertEqual(save_slot_grid_position(7), (6, 0))
        self.assertEqual(save_slot_grid_position(8), (0, 1))
        self.assertEqual(save_slot_grid_position(14), (6, 1))
        self.assertEqual(save_slot_grid_position(15), (0, 2))

    def test_save_slot_grid_position_clamps_high_columns(self) -> None:
        """Out-of-range slot values should clamp to the max configured column."""
        self.assertEqual(save_slot_grid_position(22), (0, 2))
        self.assertEqual(save_slot_grid_position(999), (4, 2))

    def test_save_slot_grid_position_handles_non_positive(self) -> None:
        """Non-positive slots should map to first grid cell."""
        self.assertEqual(save_slot_grid_position(0), (0, 0))
        self.assertEqual(save_slot_grid_position(-10), (0, 0))


class TestNetworkHelpers(unittest.TestCase):
    def test_build_retry_session_sets_user_agent(self) -> None:
        """Shared session builder should set caller-provided user agent header."""
        session = build_retry_session(user_agent="FS25-Test-Agent")
        try:
            self.assertEqual(session.headers.get("User-Agent"), "FS25-Test-Agent")
        finally:
            session.close()

    def test_build_retry_session_mounts_http_and_https_adapters(self) -> None:
        """Helper should configure adapters for both HTTP and HTTPS requests."""
        session = build_retry_session(user_agent="FS25-Test-Agent")
        try:
            self.assertIn("http://", session.adapters)
            self.assertIn("https://", session.adapters)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()