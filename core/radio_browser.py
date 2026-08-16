"""Station directory lookup backed by the free Radio Browser API."""
from __future__ import annotations

import requests

from core.logging_utils import get_logger
from core.scraper_common import build_session

logger = get_logger("core.radio_browser")


class RadioBrowser:
    """Search public radio stations. No API key required."""

    BASE_URL = "https://all.api.radio-browser.info/json"
    PAGE_SIZE = 12

    @staticmethod
    def _parse_stations(payload: object) -> list[dict[str, object]]:
        """Keep only stations the game can actually play.

        FS25 streams plain MP3/AAC; HLS playlists (.m3u8) silently fail in
        game, so they are dropped here rather than added and left broken.
        """
        if not isinstance(payload, list):
            return []

        stations: list[dict[str, object]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url_resolved") or item.get("url") or "").strip()
            name = str(item.get("name") or "").strip()
            if not url or not name:
                continue
            if item.get("hls") in (1, "1", True) or url.lower().endswith(".m3u8"):
                continue

            stations.append({
                "name": name,
                "url": url,
                "country": str(item.get("countrycode") or "").strip(),
                "codec": str(item.get("codec") or "").strip(),
                "bitrate": int(item.get("bitrate") or 0),
                "tags": str(item.get("tags") or "").strip(),
                "homepage": str(item.get("homepage") or "").strip(),
            })
        return stations

    def search(self, query: str = "", page: int = 0, limit: int = PAGE_SIZE) -> list[dict[str, object]]:
        """Fetch one page of stations, most-played first."""
        params = {
            "limit": str(limit),
            "offset": str(max(page, 0) * limit),
            "hidebroken": "true",
            "order": "clickcount",
            "reverse": "true",
        }
        query = (query or "").strip()
        if query:
            params["name"] = query

        try:
            with build_session("FS25-Mod-Manager/RadioBrowser") as session:
                response = session.get(f"{self.BASE_URL}/stations/search", params=params, timeout=20)
                response.raise_for_status()
                return self._parse_stations(response.json())
        except (requests.RequestException, ValueError) as exc:
            logger.warning("radio search failed for %r: %s", query, exc)
            raise
