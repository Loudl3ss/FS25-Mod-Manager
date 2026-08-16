"""Tests for shared UI helper modules introduced during refactors."""

import unittest

from ui.network_helpers import build_retry_session


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