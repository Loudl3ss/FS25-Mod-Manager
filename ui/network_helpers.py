"""Shared HTTP/network helpers for UI worker threads."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def build_retry_session(
    *,
    user_agent: str,
    total_retries: int = 3,
    backoff_factor: float = 0.6,
    pool_connections: int = 10,
    pool_maxsize: int = 10,
) -> requests.Session:
    """Create a requests session with retry/backoff defaults for flaky endpoints."""
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session
