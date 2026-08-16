"""Shared HTTP/network helpers for UI worker threads."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def build_retry_session(*, user_agent: str) -> requests.Session:
    """Create a requests session with retry/backoff defaults for flaky endpoints."""
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
        ),
        pool_connections=10,
        pool_maxsize=10,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session
