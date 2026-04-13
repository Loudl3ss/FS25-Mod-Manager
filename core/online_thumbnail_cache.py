"""Persistent thumbnail cache for online mod listings."""
from __future__ import annotations

import hashlib
from pathlib import Path


class OnlineThumbnailCache:
    """Simple file-based cache keyed by thumbnail URL hash."""

    def __init__(self, cache_dir: str | None = None):
        if cache_dir is None:
            cache_dir = str(Path.home() / ".cache" / "fs25-mod-manager" / "online-thumbnails")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_url(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.bin"

    def get(self, url: str) -> bytes | None:
        if not url:
            return None
        path = self._path_for_url(url)
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    def set(self, url: str, data: bytes):
        if not url or not data:
            return
        path = self._path_for_url(url)
        try:
            path.write_bytes(data)
        except OSError:
            # Best-effort cache only.
            return
