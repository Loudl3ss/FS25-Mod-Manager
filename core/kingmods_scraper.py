"""Scraper service for KingMods FS25 pages."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.logging_utils import get_logger

logger = get_logger("core.kingmods_scraper")


class KingModsScraper:
    """Scraper service for KingMods FS25 listings/details/downloads."""

    BASE_URL = "https://www.kingmods.net"
    DEFAULT_FILTER = "new-mods"
    CATEGORIES_URL = "https://www.kingmods.net/en/fs25/categories"

    _REQUESTED_CATEGORY_TREE: list[dict[str, object]] = [
        {"label": "New", "filter": "new-mods", "children": []},
        {"label": "Trending", "filter": "trending-mods", "children": []},
        {
            "label": "Tractors",
            "filter": "",
            "children": [
                {"label": "Small Tractors", "slug": "small-tractors"},
                {"label": "Medium Tractors", "slug": "medium-tractors"},
                {"label": "Large Tractors", "slug": "large-tractors"},
            ],
        },
        {
            "label": "Combine & Forage Harvesting",
            "filter": "",
            "children": [
                {"label": "Combine Harvesters", "slug": "combine-harvesters"},
                {"label": "Forage Harvesters", "slug": "forage-harvesters"},
                {"label": "Cutter Headers", "slug": "cutter-headers"},
                {"label": "Header Trailers", "slug": "header-trailers"},
            ],
        },
        {
            "label": "Trailers",
            "filter": "",
            "children": [
                {"label": "Trailers", "slug": "trailers"},
                {"label": "Forage Wagons", "slug": "forage-wagons"},
                {"label": "Auger Wagons", "slug": "auger-wagons"},
                {"label": "Low Loaders Trailers", "slug": "low-loaders-trailers"},
                {"label": "Semi Trailers", "slug": "semi-trailers"},
            ],
        },
        {
            "label": "Vehicles",
            "filter": "",
            "children": [
                {"label": "Trucks", "slug": "trucks"},
                {"label": "Cars", "slug": "cars"},
                {"label": "Other Vehicles", "slug": "other-vehicles"},
            ],
        },
        {
            "label": "Field Work",
            "filter": "",
            "children": [
                {"label": "Plows", "slug": "plows"},
                {"label": "Cultivators", "slug": "cultivators"},
                {"label": "Subsoilers", "slug": "subsoilers"},
                {"label": "Seeders", "slug": "seeders"},
                {"label": "Planters", "slug": "planters"},
                {"label": "Power Harrows", "slug": "power-harrows"},
                {"label": "Rollers", "slug": "rollers"},
                {"label": "Beaker Machines", "slug": "bale-machines"},
                {"label": "Stone Pickers", "slug": "stone-pickers"},
            ],
        },
        {
            "label": "Fertilization",
            "filter": "",
            "children": [
                {"label": "Manure Spreaders", "slug": "manure-spreaders"},
                {"label": "Slurry Tanks", "slug": "slurry-tanks"},
                {"label": "Fertilizer Spreaders", "slug": "fertilizer-spreaders"},
                {"label": "Sprayers", "slug": "sprayers"},
                {"label": "Weeders", "slug": "weeders"},
            ],
        },
        {
            "label": "Grassland",
            "filter": "",
            "children": [
                {"label": "Windrowers", "slug": "windrowers"},
                {"label": "Tedders", "slug": "tedders"},
                {"label": "Mowers", "slug": "mowers"},
                {"label": "Mulchers", "slug": "mulchers"},
            ],
        },
    ]

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": "FS25-Mod-Manager/KingModsScraper"})
        return session

    def _filter_to_url(self, filter_key: str, page: int) -> str:
        key = (filter_key or self.DEFAULT_FILTER).strip()
        if key.startswith("http://") or key.startswith("https://"):
            base = key
        elif key.startswith("/"):
            base = urljoin(self.BASE_URL, key)
        else:
            base = f"{self.BASE_URL}/en/fs25/{key}"

        if page <= 0:
            return base

        parsed = urlparse(base)
        query = parse_qs(parsed.query)
        # KingMods starts pagination at page=2 for the second page.
        query["page"] = [str(page + 1)]
        encoded_query = "&".join(f"{k}={v[-1]}" for k, v in query.items() if v)
        parsed = parsed._replace(query=encoded_query)
        return parsed.geturl()

    def _normalize_label(self, text: str) -> str:
        lowered = text.lower().strip()
        lowered = re.sub(r"\b\d+[\s,.]*(mods?|mod)\b", "", lowered)
        lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
        return " ".join(lowered.split())

    def _slug_to_label(self, slug: str) -> str:
        return slug.replace("-", " ").title()

    def _extract_category_name(self, filter_key: str) -> str:
        """Extract a human-readable category name from filter_key (could be URL or slug)."""
        if not filter_key:
            return "Unknown"
        
        # If it's a URL, try to extract category from query parameters
        if "http" in filter_key or filter_key.startswith("/"):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(filter_key)
            params = parse_qs(parsed.query)
            
            # Try to get 'type' parameter (e.g., type=trailers)
            if "type" in params:
                type_val = params["type"][0]
                return type_val.replace("-", " ").title()
            
            # Fallback: extract from path
            path = parsed.path.rstrip("/")
            if path:
                parts = path.split("/")
                if parts:
                    last = parts[-1]
                    if last:
                        return last.replace("-", " ").title()
        
        # It's a slug, convert it
        return self._slug_to_label(filter_key)

    def _extract_categories_lookup(self, soup: BeautifulSoup) -> dict[str, dict[str, str]]:
        """Build a lookup keyed by category slug with best-effort human labels and URLs."""
        lookup: dict[str, dict[str, str]] = {}

        for anchor in soup.select("a[href*='/en/fs25/categories/']"):
            href = str(anchor.get("href", "")).strip()
            if not href:
                continue

            abs_url = urljoin(self.BASE_URL, href)
            parsed = urlparse(abs_url)
            path = parsed.path.rstrip("/")
            marker = "/en/fs25/categories/"
            if marker not in path:
                continue

            subpath = path.split(marker, 1)[1]
            parts = [p for p in subpath.split("/") if p]
            if len(parts) != 2:
                continue

            group_slug, category_slug = parts
            raw_label = anchor.get_text(" ", strip=True)
            cleaned_label = re.sub(r"\b\d+[\s,.]*(mods?|mod)\b", "", raw_label, flags=re.IGNORECASE).strip()
            label = cleaned_label if cleaned_label else self._slug_to_label(category_slug)

            lookup[category_slug] = {
                "group": group_slug,
                "label": label,
                "filter": abs_url,
            }

        return lookup

    def _build_requested_tree(self, lookup: dict[str, dict[str, str]]) -> list[dict[str, object]]:
        tree: list[dict[str, object]] = []

        for node in self._REQUESTED_CATEGORY_TREE:
            label = str(node.get("label", "")).strip()
            children = node.get("children", [])
            if not isinstance(children, list):
                children = []

            if not children:
                tree.append(
                    {
                        "label": label,
                        "filter": str(node.get("filter", "")).strip(),
                        "children": [],
                    }
                )
                continue

            resolved_children: list[dict[str, str]] = []
            for child in children:
                child_label = str(child.get("label", "")).strip()
                child_slug = str(child.get("slug", "")).strip()
                if not child_label or not child_slug:
                    continue

                hit = lookup.get(child_slug)
                if hit is not None:
                    resolved_children.append(
                        {
                            "label": child_label,
                            "filter": str(hit.get("filter", "")).strip(),
                        }
                    )

            if resolved_children:
                tree.append(
                    {
                        "label": label,
                        "filter": "",
                        "children": resolved_children,
                    }
                )

        return tree

    def fetch_mods(self, filter_key: str = "new-mods", page: int = 0) -> list[dict[str, object]]:
        """Fetch KingMods cards for a specific filter and page."""
        url = self._filter_to_url(filter_key, page)
        try:
            with self._build_session() as session:
                response = session.get(url, timeout=20)
                response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("fetch_mods failed for filter=%s page=%s: %s", filter_key, page, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        mods: list[dict[str, object]] = []
        seen: set[str] = set()

        for link_el in soup.select("a[href*='/en/fs25/mods/'][title]"):
            href = str(link_el.get("href", "")).strip()
            if not href:
                continue
            details_url = urljoin(self.BASE_URL, href)

            id_match = re.search(r"/mods/(\d+)", details_url)
            mod_id = id_match.group(1) if id_match else details_url
            if mod_id in seen:
                continue

            img_el = link_el.select_one("img")
            thumb_url = ""
            if img_el is not None:
                thumb_src = str(img_el.get("src", "")).strip()
                if "/uploads/fs25/mods/" in thumb_src:
                    thumb_url = urljoin(self.BASE_URL, thumb_src)
            if not thumb_url:
                continue

            title = str(link_el.get("title", "")).strip() or "Unknown"

            # Extract category name from filter_key (could be URL or slug)
            category_name = self._extract_category_name(filter_key)

            mods.append(
                {
                    "id": mod_id,
                    "title": title,
                    "author": "KingMods",
                    "category": category_name,
                    "details_url": details_url,
                    "thumbnail_url": thumb_url,
                }
            )
            seen.add(mod_id)

        return mods

    def fetch_category_tree(self) -> list[dict[str, object]]:
        """Return requested category tree plus extra categories discovered on KingMods."""
        try:
            with self._build_session() as session:
                response = session.get(self.CATEGORIES_URL, timeout=20)
                response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("fetch_category_tree failed: %s", exc)
            return [
                {"label": node["label"], "filter": str(node.get("filter", "")), "children": list(node.get("children", []))}
                for node in self._REQUESTED_CATEGORY_TREE
            ]

        soup = BeautifulSoup(response.text, "html.parser")
        lookup = self._extract_categories_lookup(soup)
        requested_tree = self._build_requested_tree(lookup)

        used_slugs: set[str] = set()
        for group in requested_tree:
            for child in group.get("children", []):
                child_filter = str(child.get("filter", "")).strip()
                for slug, info in lookup.items():
                    if str(info.get("filter", "")).strip() == child_filter:
                        used_slugs.add(slug)
                        break

        extras_by_group: dict[str, list[dict[str, str]]] = {}
        for slug, info in lookup.items():
            if slug in used_slugs:
                continue
            group_slug = str(info.get("group", "")).strip()
            if not group_slug:
                continue

            extras_by_group.setdefault(group_slug, []).append(
                {
                    "label": str(info.get("label", self._slug_to_label(slug))).strip(),
                    "filter": str(info.get("filter", "")).strip(),
                }
            )

        extra_groups: list[dict[str, object]] = []
        for group_slug, children in sorted(extras_by_group.items()):
            if not children:
                continue

            unique_children: list[dict[str, str]] = []
            seen_filters: set[str] = set()
            for child in children:
                filt = str(child.get("filter", "")).strip()
                if not filt or filt in seen_filters:
                    continue
                seen_filters.add(filt)
                unique_children.append(child)

            if unique_children:
                extra_groups.append(
                    {
                        "label": self._slug_to_label(group_slug),
                        "filter": "",
                        "children": sorted(unique_children, key=lambda c: self._normalize_label(str(c.get("label", "")))),
                    }
                )

        return requested_tree + extra_groups

    def fetch_category_filters(self) -> list[dict[str, str]]:
        """Return available flat filters for compatibility."""
        flat: list[dict[str, str]] = []
        seen: set[str] = set()

        for node in self.fetch_category_tree():
            node_filter = str(node.get("filter", "")).strip()
            node_label = str(node.get("label", "")).strip()
            if node_filter and node_filter not in seen:
                flat.append({"label": node_label, "filter": node_filter})
                seen.add(node_filter)

            children = node.get("children", [])
            if not isinstance(children, list):
                continue
            for child in children:
                child_filter = str(child.get("filter", "")).strip()
                child_label = str(child.get("label", "")).strip()
                if child_filter and child_filter not in seen:
                    flat.append({"label": child_label, "filter": child_filter})
                    seen.add(child_filter)

        return flat

    def fetch_mod_details(self, details_url: str) -> dict[str, object]:
        """Fetch detail-page data for a single KingMods mod."""
        try:
            with self._build_session() as session:
                response = session.get(details_url, timeout=20)
                response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("fetch_mod_details failed for %s: %s", details_url, exc)
            return {}

        soup = BeautifulSoup(response.text, "html.parser")

        title_el = soup.select_one("h1")
        title = title_el.get_text(" ", strip=True) if title_el else "Unknown"

        desc_meta = soup.select_one("meta[name='description']")
        description = str(desc_meta.get("content", "")).strip() if desc_meta else ""
        if not description:
            description = "No description available."

        author = ""
        author_link = soup.select_one("a[href*='/en/profile/']")
        if author_link is not None:
            author = author_link.get_text(" ", strip=True)

        rating = ""
        rating_match = re.search(r"(\d(?:\.\d)?)\s*stars?", soup.get_text(" ", strip=True), re.IGNORECASE)
        if rating_match:
            rating = rating_match.group(1)

        version = ""
        download_el = None
        for anchor in soup.select("a.btn.btn-lg.btn-brand[href]"):
            text = anchor.get_text(" ", strip=True)
            if "download" in text.lower():
                download_el = anchor
                version_match = re.search(r"V\s*([\d.]+)", text, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                break

        released = ""
        time_el = soup.select_one("time[datetime]")
        if time_el is not None:
            released = str(time_el.get("datetime", "")).strip()

        thumb = ""
        og_img = soup.select_one("meta[property='og:image']")
        if og_img is not None:
            thumb = urljoin(self.BASE_URL, str(og_img.get("content", "")).strip())

        download_url = ""
        if download_el is not None:
            download_url = urljoin(self.BASE_URL, str(download_el.get("href", "")).strip())

        details: dict[str, object] = {
            "title": title,
            "author": author,
            "category": "KingMods",
            "version": version,
            "released": released,
            "platform": "PC/MAC",
            "rating": rating,
            "description": description,
            "download_url": download_url,
            "details_url": details_url,
        }

        if thumb:
            details["thumbnail_url"] = thumb

        return details

    def download_mod(self, download_url: str, target_dir: str, referer_url: str = "", filename: str = "") -> str:
        """Download a mod zip/file into target directory and return saved path."""
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        parsed = urlparse(download_url)
        fallback_name = Path(parsed.path).name or "kingmods-download.zip"
        resolved_name = filename.strip() if filename else fallback_name
        if not Path(resolved_name).suffix:
            resolved_name = f"{resolved_name}.zip"

        destination = Path(target_dir) / resolved_name
        temp_destination = destination.with_suffix(destination.suffix + ".part")

        try:
            with self._build_session() as session:
                headers = {"Referer": referer_url} if referer_url else None
                with session.get(download_url, headers=headers, timeout=90, stream=True, allow_redirects=True) as response:
                    response.raise_for_status()
                    with open(temp_destination, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                handle.write(chunk)
        except (requests.RequestException, OSError) as exc:
            logger.warning("download_mod failed for %s: %s", download_url, exc)
            raise

        temp_destination.replace(destination)
        return str(destination)
