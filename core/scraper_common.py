"""Shared HTTP/session/download helpers for the mod scrapers."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from core.logging_utils import get_logger

logger = get_logger("core.scraper_common")


def build_session(user_agent: str) -> requests.Session:
    """Build an HTTP session identifying this app."""
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    return session


def flatten_category_tree(tree: list[dict[str, object]]) -> list[dict[str, str]]:
    """Flatten a nested category tree into unique {label, filter} entries."""
    flat: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(node: object) -> None:
        if not isinstance(node, dict):
            return
        label = str(node.get("label", "")).strip()
        filter_key = str(node.get("filter", "")).strip()
        if label and filter_key and filter_key not in seen:
            seen.add(filter_key)
            flat.append({"label": label, "filter": filter_key})

    for node in tree:
        add(node)
        children = node.get("children", []) if isinstance(node, dict) else []
        if isinstance(children, list):
            for child in children:
                add(child)

    return flat


def download_mod(
    session: requests.Session,
    download_url: str,
    target_dir: str,
    *,
    referer_url: str = "",
    filename: str = "",
    default_name: str = "mod.zip",
    timeout: int = 60,
) -> str:
    """Stream a mod file into target_dir via a .part file. Returns the saved path."""
    if not download_url:
        raise ValueError("Download URL is empty")

    Path(target_dir).mkdir(parents=True, exist_ok=True)

    name = filename.strip() or Path(urlparse(download_url).path).name or default_name
    if not Path(name).suffix:
        name = f"{name}.zip"

    destination = Path(target_dir) / name
    part = destination.with_suffix(destination.suffix + ".part")

    try:
        with session.get(download_url, headers={"Referer": referer_url} if referer_url else None,
                         timeout=timeout, stream=True) as response:
            response.raise_for_status()
            with open(part, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        handle.write(chunk)
    except (requests.RequestException, OSError) as exc:
        logger.warning("download_mod failed for %s: %s", download_url, exc)
        part.unlink(missing_ok=True)
        raise

    part.replace(destination)
    return str(destination)
