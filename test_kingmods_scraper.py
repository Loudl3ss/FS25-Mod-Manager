"""Tests for KingModsScraper network error fallback behavior."""

from __future__ import annotations

import tempfile
import unittest

import requests

from core.kingmods_scraper import KingModsScraper


class _FailingSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        raise requests.RequestException("network failed")


class TestKingModsScraper(unittest.TestCase):
    def test_fetch_mods_returns_empty_on_request_failure(self) -> None:
        scraper = KingModsScraper()
        scraper._build_session = lambda: _FailingSession()  # type: ignore[method-assign]

        self.assertEqual(scraper.fetch_mods(), [])

    def test_fetch_mod_details_returns_empty_on_request_failure(self) -> None:
        scraper = KingModsScraper()
        scraper._build_session = lambda: _FailingSession()  # type: ignore[method-assign]

        self.assertEqual(scraper.fetch_mod_details("https://www.kingmods.net/en/fs25/mods/12345"), {})

    def test_fetch_category_tree_falls_back_to_requested_tree(self) -> None:
        scraper = KingModsScraper()
        scraper._build_session = lambda: _FailingSession()  # type: ignore[method-assign]

        tree = scraper.fetch_category_tree()
        self.assertTrue(isinstance(tree, list))
        self.assertGreater(len(tree), 0)

    def test_download_mod_raises_request_error(self) -> None:
        scraper = KingModsScraper()
        scraper._build_session = lambda: _FailingSession()  # type: ignore[method-assign]

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(requests.RequestException):
                scraper.download_mod(
                    "https://www.kingmods.net/en/dl/mod.zip",
                    tmpdir,
                    filename="mod.zip",
                )


if __name__ == "__main__":
    unittest.main()
