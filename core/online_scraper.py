"""Isolated online scraper architecture for FS25 ModHub pages."""
from __future__ import annotations

from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.scraper_common import build_session, download_mod, flatten_category_tree


class FarmingSimulatorScraper:
    """Scraper service for Farming Simulator 25 online mod listings."""

    BASE_URL = "https://www.farming-simulator.com/mods.php"

    def _build_session(self) -> requests.Session:
        return build_session("FS25-Mod-Manager/OnlineScraper")

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

    def fetch_category_filters(self) -> list[dict[str, str]]:
        """Discover available FS25 category filters from the ModHub menu."""
        return flatten_category_tree(self.fetch_category_tree())

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
        with self._build_session() as session:
            return download_mod(session, download_url, target_dir,
                                referer_url=referer_url, filename=filename)
