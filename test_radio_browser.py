"""Tests for Radio Browser result filtering."""
import unittest

from core.radio_browser import RadioBrowser


class TestParseStations(unittest.TestCase):
    def test_drops_hls_streams_the_game_cannot_play(self):
        payload = [
            {"name": "Plain MP3", "url_resolved": "http://a/x.mp3", "hls": 0},
            {"name": "HLS flagged", "url_resolved": "http://b/x", "hls": 1},
            {"name": "HLS by suffix", "url_resolved": "http://c/chunks.m3u8", "hls": 0},
        ]
        names = [s["name"] for s in RadioBrowser._parse_stations(payload)]
        self.assertEqual(names, ["Plain MP3"])

    def test_skips_entries_without_a_name_or_url(self):
        payload = [
            {"name": "", "url_resolved": "http://a/x.mp3"},
            {"name": "No url", "url_resolved": ""},
            {"name": "Good", "url_resolved": "http://d/x.aac"},
        ]
        self.assertEqual(len(RadioBrowser._parse_stations(payload)), 1)

    def test_falls_back_to_url_when_resolved_missing(self):
        stations = RadioBrowser._parse_stations([{"name": "S", "url": "http://e/x.mp3"}])
        self.assertEqual(stations[0]["url"], "http://e/x.mp3")

    def test_normalises_metadata_types(self):
        stations = RadioBrowser._parse_stations(
            [{"name": "S", "url_resolved": "http://f/x.mp3",
              "countrycode": "DE", "codec": "MP3", "bitrate": "128"}]
        )
        self.assertEqual(stations[0]["bitrate"], 128)
        self.assertEqual(stations[0]["country"], "DE")

    def test_tolerates_a_non_list_payload(self):
        self.assertEqual(RadioBrowser._parse_stations({"error": "nope"}), [])


if __name__ == "__main__":
    unittest.main()
