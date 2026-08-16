"""Tests for the shared scraper helpers."""
import tempfile
import unittest
from pathlib import Path

import requests

from core.scraper_common import download_mod, flatten_category_tree


class _FakeResponse:
    def __init__(self, chunks, error=None):
        self._chunks = chunks
        self._error = error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self._error:
            raise self._error

    def iter_content(self, chunk_size=0):
        return iter(self._chunks)


class _FakeSession:
    def __init__(self, chunks=(b"data",), error=None):
        self._chunks = chunks
        self._error = error
        self.last_headers = None

    def get(self, url, headers=None, timeout=None, stream=False):
        self.last_headers = headers
        return _FakeResponse(self._chunks, self._error)


class TestFlattenCategoryTree(unittest.TestCase):
    def test_flattens_children_and_dedupes(self):
        tree = [
            {"label": "New", "filter": "new", "children": []},
            {"label": "Tractors", "filter": "", "children": [
                {"label": "Small", "filter": "small"},
                {"label": "New again", "filter": "new"},
            ]},
        ]
        self.assertEqual(
            flatten_category_tree(tree),
            [{"label": "New", "filter": "new"}, {"label": "Small", "filter": "small"}],
        )

    def test_skips_entries_without_label_or_filter(self):
        tree = [{"label": "", "filter": "x", "children": [{"label": "y", "filter": ""}]}]
        self.assertEqual(flatten_category_tree(tree), [])


class TestDownloadMod(unittest.TestCase):
    def test_writes_file_and_removes_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = download_mod(_FakeSession([b"ab", b"cd"]), "https://x/y/mod.zip", tmp)
            self.assertEqual(Path(path).read_bytes(), b"abcd")
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["mod.zip"])

    def test_appends_zip_suffix_and_uses_default_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = download_mod(_FakeSession(), "https://x/", tmp, default_name="fallback")
            self.assertEqual(Path(path).name, "fallback.zip")
            path = download_mod(_FakeSession(), "https://x/get/mod123", tmp)
            self.assertEqual(Path(path).name, "mod123.zip")

    def test_cleans_up_part_file_on_failure(self):
        session = _FakeSession(error=requests.RequestException("boom"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(requests.RequestException):
                download_mod(session, "https://x/mod.zip", tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_rejects_empty_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download_mod(_FakeSession(), "", tmp)

    def test_sends_referer_only_when_given(self):
        session = _FakeSession()
        with tempfile.TemporaryDirectory() as tmp:
            download_mod(session, "https://x/a.zip", tmp, referer_url="https://x/page")
            self.assertEqual(session.last_headers, {"Referer": "https://x/page"})
            download_mod(session, "https://x/b.zip", tmp)
            self.assertIsNone(session.last_headers)


if __name__ == "__main__":
    unittest.main()
