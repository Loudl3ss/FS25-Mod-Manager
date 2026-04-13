"""Isolated online scraper architecture for FS25 ModHub pages."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class FarmingSimulatorScraper:
    """Scraper service for Farming Simulator 25 online mod listings."""

    BASE_URL = "https://www.farming-simulator.com/mods.php"

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": "FS25-Mod-Manager/OnlineScraper"})
        return session

    def fetch_mods(self, filter_key: str = "latest", page: int = 0) -> list[dict[str, object]]:
        """Fetch FS25 mod cards for a specific filter and page."""
        params = {
            "title": "fs2025",
            "filter": filter_key,
            "page": str(page),
        }
        with self._build_session() as session:
            response = session.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.mod-item")
        mods: list[dict[str, object]] = []

        for card in cards:
            title_el = card.select_one("div.mod-item__content h4")
            author_el = card.select_one("div.mod-item__content p span")
            label_el = card.select_one("div.mod-item__img div.mod-label")
            link_el = card.select_one("a[href*='mod.php?mod_id=']")
            thumb_el = card.select_one("div.mod-item__img img")

            title = title_el.get_text(strip=True) if title_el else "Unknown"
            author_raw = author_el.get_text(strip=True) if author_el else "Unknown"
            author = author_raw.replace("By:", "", 1).strip()
            category = label_el.get_text(strip=True) if label_el else "Latest"
            details_url = ""
            thumbnail_url = ""
            mod_id = ""

            if link_el and link_el.get("href"):
                details_url = urljoin("https://www.farming-simulator.com/", str(link_el.get("href", "")))
                parsed = urlparse(details_url)
                mod_id = parse_qs(parsed.query).get("mod_id", [""])[0]

            if thumb_el and thumb_el.get("src"):
                thumbnail_url = urljoin("https://www.farming-simulator.com/", str(thumb_el.get("src", "")))

            mods.append(
                {
                    "id": mod_id or details_url or title,
                    "title": title,
                    "author": author,
                    "category": category,
                    "details_url": details_url,
                    "thumbnail_url": thumbnail_url,
                }
            )

        return mods

    def fetch_latest_mods(self, page: int = 0) -> list[dict[str, object]]:
        """Backward-compatible helper for latest mods."""
        return self.fetch_mods(filter_key="latest", page=page)

    def fetch_category_filters(self) -> list[dict[str, str]]:
        """Discover available FS25 category filters from the ModHub menu."""
        tree = self.fetch_category_tree()
        flat: list[dict[str, str]] = []
        seen: set[str] = set()

        for item in tree:
            filter_key = str(item.get("filter", "")).strip()
            label = str(item.get("label", "")).strip()
            if filter_key and label and filter_key not in seen:
                flat.append({"label": label, "filter": filter_key})
                seen.add(filter_key)

            for child in item.get("children", []):
                child_filter = str(child.get("filter", "")).strip()
                child_label = str(child.get("label", "")).strip()
                if child_filter and child_label and child_filter not in seen:
                    flat.append({"label": child_label, "filter": child_filter})
                    seen.add(child_filter)

        return flat

    def fetch_category_tree(self) -> list[dict[str, object]]:
        """Discover FS25 category hierarchy (top-level + nested subcategories)."""
        params = {
            "title": "fs2025",
            "filter": "latest",
            "page": "0",
        }

        with self._build_session() as session:
            response = session.get(self.BASE_URL, params=params, timeout=20)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        root = soup.select_one("ul.menu-dropdown.large.multilevel")
        if root is None:
            return []

        def parse_filter(href: str) -> str:
            full = urljoin("https://www.farming-simulator.com/", href)
            query = parse_qs(urlparse(full).query)
            if query.get("title", [""])[0] != "fs2025":
                return ""
            return query.get("filter", [""])[0]

        tree: list[dict[str, object]] = []
        for li in root.find_all("li", recursive=False):
            anchor = li.find("a", class_="menu-link", recursive=False)
            if anchor is None:
                continue

            label = anchor.get_text(" ", strip=True)
            if not label:
                continue

            classes = anchor.get("class", [])
            href = str(anchor.get("href", ""))
            item: dict[str, object] = {
                "label": label,
                "filter": "",
                "children": [],
            }

            if "menu-submenu" in classes:
                child_ul = li.find("ul", class_="menu-list", recursive=False)
                if child_ul is not None:
                    children: list[dict[str, str]] = []
                    for child_li in child_ul.find_all("li", recursive=False):
                        child_anchor = child_li.find("a", class_="menu-link", recursive=False)
                        if child_anchor is None:
                            continue
                        child_label = child_anchor.get_text(" ", strip=True)
                        child_href = str(child_anchor.get("href", ""))
                        child_filter = parse_filter(child_href)
                        if child_label and child_filter:
                            children.append({"label": child_label, "filter": child_filter})
                    item["children"] = children
            else:
                item["filter"] = parse_filter(href)

            tree.append(item)

        return tree

    def fetch_mod_details(self, details_url: str) -> dict[str, object]:
        """Fetch detail-page data for a single ModHub mod."""
        with self._build_session() as session:
            response = session.get(details_url, timeout=20)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title_el = soup.select_one("h1, h2")
        desc_el = soup.select_one("div.medium-12.large-8.columns div.top-line")
        rating_el = soup.select_one("div.mod-item__rating-num")
        download_el = soup.select_one("div.download-box a[href]")

        details: dict[str, object] = {
            "title": title_el.get_text(strip=True) if title_el else "Unknown",
            "description": "\n".join(desc_el.stripped_strings) if desc_el else "No description available.",
            "rating": rating_el.get_text(" ", strip=True) if rating_el else "",
            "download_url": urljoin(details_url, str(download_el.get("href", ""))) if download_el and download_el.get("href") else "",
            "details_url": details_url,
        }

        for row in soup.select("div.table-game-info div.table-row"):
            cells = row.select("div.table-cell")
            if len(cells) < 2:
                continue
            key = cells[0].get_text(" ", strip=True).rstrip(":")
            value = cells[1].get_text(" ", strip=True)
            if key:
                details[key.lower()] = value

        return details

    def download_mod(self, download_url: str, target_dir: str, referer_url: str = "", filename: str = "") -> str:
        """Download a mod zip into the target directory and return its saved path."""
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        resolved_name = filename.strip() if filename else Path(urlparse(download_url).path).name
        if not resolved_name:
            raise ValueError("Unable to determine download filename")

        destination = Path(target_dir) / resolved_name
        temp_destination = destination.with_suffix(destination.suffix + ".part")

        with self._build_session() as session:
            headers = {"Referer": referer_url} if referer_url else None
            with session.get(download_url, headers=headers, timeout=60, stream=True) as response:
                response.raise_for_status()
                with open(temp_destination, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            handle.write(chunk)

        temp_destination.replace(destination)
        return str(destination)
