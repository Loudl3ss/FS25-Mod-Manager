"""Scraper service for FS25.NET FS25 pages."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class FS25NetScraper:
    """Scraper service for FS25.NET FS25 listings/details/downloads."""

    BASE_URL = "https://fs25.net"
    BASE_CATEGORY_URL = "https://fs25.net/category/farming-simulator-25-mods/"
    DEFAULT_FILTER = "latest"
    CATEGORIES_URL = BASE_CATEGORY_URL

    _REQUESTED_CATEGORY_TREE: list[dict[str, object]] = [
        {"label": "Cars", "slug": "cars", "children": []},
        {"label": "Combines", "slug": "combines", "children": []},
        {"label": "Cranes", "slug": "cranes", "children": []},
        {"label": "Forestry", "slug": "forestry", "children": []},
        {
            "label": "Forklifts and Excavators",
            "slug": "forklifts-and-excavators",
            "children": [],
        },
        {
            "label": "Implements and Tools",
            "slug": "implements-and-tools",
            "children": [
                {"label": "Attachments", "slug": "attachments"},
                {"label": "Cultivators and Harrows", "slug": "cultivators-and-harrows"},
                {"label": "Front loader", "slug": "front-loader"},
                {"label": "Headers", "slug": "headers"},
                {"label": "Mowers", "slug": "mowers"},
                {"label": "Other", "slug": "other"},
                {"label": "Ploughs", "slug": "ploughs"},
                {"label": "Seeders", "slug": "seeders"},
                {"label": "Sprayers", "slug": "sprayers"},
                {"label": "Spreaders", "slug": "spreaders"},
                {"label": "Stone Collectors", "slug": "stone-collectors"},
                {"label": "Tedders", "slug": "tedders"},
                {"label": "Weights", "slug": "weights"},
            ],
        },
        {
            "label": "Maps",
            "slug": "maps",
            "children": [
                {"label": "AutoDrive", "slug": "autodrive"},
            ],
        },
        {"label": "News", "slug": "news", "children": []},
        {"label": "Objects", "slug": "objects", "children": []},
        {"label": "Other", "slug": "other", "children": []},
        {"label": "Packs", "slug": "packs", "children": []},
        {"label": "Placeable Objects", "slug": "placeable-objects", "children": []},
        {"label": "Save Games", "slug": "save-games", "children": []},
        {"label": "Scripts and Tools", "slug": "scripts-and-tools", "children": []},
        {"label": "Textures", "slug": "textures", "children": []},
        {"label": "Tractors", "slug": "tractors", "children": []},
        {
            "label": "Trailers",
            "slug": "trailers",
            "children": [
                {"label": "Balers", "slug": "balers"},
                {"label": "Liquid Manure", "slug": "liquid-manure"},
                {"label": "Livestock", "slug": "livestock"},
                {"label": "Silage", "slug": "silage"},
            ],
        },
        {"label": "Trucks", "slug": "trucks", "children": []},
        {"label": "Tutorials", "slug": "tutorials", "children": []},
        {"label": "Vehicles", "slug": "vehicles", "children": []},
        {"label": "Wardrobe", "slug": "wardrobe", "children": []},
    ]

    def _build_session(self) -> requests.Session:
        """Build an HTTP session with retries."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "FS25-Mod-Manager/FS25NetScraper",
            }
        )
        return session

    def _slug_to_label(self, slug: str) -> str:
        return slug.replace("-", " ").title()

    def _norm(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    def _fallback_category_url(self, slug: str) -> str:
        slug = slug.strip("/")
        if not slug:
            return self.BASE_CATEGORY_URL
        return urljoin(self.BASE_URL, f"/category/farming-simulator-25-mods/{slug}/")

    def _filter_to_url(self, filter_key: str, page: int) -> str:
        normalized = (filter_key or "").strip()

        if not normalized or normalized == "latest":
            base = self.BASE_CATEGORY_URL
        elif normalized.startswith("http://") or normalized.startswith("https://"):
            base = normalized
        else:
            base = self._fallback_category_url(normalized)

        if page <= 0:
            return base

        base = base.rstrip("/") + "/"
        return urljoin(base, f"page/{page + 1}/")

    def _extract_category_name(self, filter_key: str) -> str:
        """Extract a human-readable category name from filter_key (could be URL or slug)."""
        if not filter_key:
            return "Unknown"

        # If it's a URL, try to extract category from the path
        if "http" in filter_key or filter_key.startswith("/"):
            parsed = urlparse(filter_key)
            path = parsed.path.rstrip("/")
            if path:
                parts = path.split("/")
                if parts:
                    last = parts[-1]
                    if last and last not in ["mods", "categories"]:
                        return last.replace("-", " ").title()
        
        # It's a slug, convert it
        return self._slug_to_label(filter_key)

    def _extract_categories_lookup(self, soup: BeautifulSoup) -> dict[str, dict[str, str]]:
        """Build a lookup keyed by category slug with labels and URLs."""
        lookup: dict[str, dict[str, str]] = {}

        # Try to find category links on categories page
        for anchor in soup.select("a[href*='/category/'], a[href*='/categories/']"):
            href = str(anchor.get("href", "")).strip()
            if not href:
                continue

            abs_url = urljoin(self.BASE_URL, href)
            parsed = urlparse(abs_url)
            path = parsed.path.rstrip("/")

            # Extract slug from URL (e.g., /category/tractors or /categories/tractors)
            parts = [p for p in path.split("/") if p and p not in ["category", "categories"]]
            if not parts:
                continue

            slug = parts[-1]
            raw_label = anchor.get_text(" ", strip=True)
            cleaned_label = re.sub(r"\b\d+[\s,.]*(mods?|mod)\b", "", raw_label, flags=re.IGNORECASE).strip()
            label = cleaned_label if cleaned_label else self._slug_to_label(slug)

            lookup[slug] = {
                "label": label,
                "filter": abs_url,
            }

        return lookup

    def _build_requested_tree(self, lookup: dict[str, dict[str, str]]) -> list[dict[str, object]]:
        tree: list[dict[str, object]] = []

        label_lookup = {
            self._norm(str(info.get("label", ""))): info for info in lookup.values()
        }

        def resolve_filter(label: str, slug: str, fallback_filter: str = "") -> str:
            if slug and slug in lookup:
                return str(lookup[slug].get("filter", "")).strip()
            if label:
                by_label = label_lookup.get(self._norm(label))
                if by_label is not None:
                    return str(by_label.get("filter", "")).strip()
            if fallback_filter:
                return fallback_filter
            if slug:
                return self._fallback_category_url(slug)
            return ""

        for node in self._REQUESTED_CATEGORY_TREE:
            label = str(node.get("label", "")).strip()
            filter_key = str(node.get("filter", "")).strip()
            slug = str(node.get("slug", "")).strip()
            raw_children = node.get("children", [])
            children_specs: list[dict[str, str]] = raw_children if isinstance(raw_children, list) else []

            if not children_specs:
                leaf_filter = resolve_filter(label, slug, filter_key)
                if leaf_filter:
                    tree.append({"label": label, "filter": leaf_filter, "children": []})
                continue

            resolved_children: list[dict[str, str]] = []
            for child_spec in children_specs:
                child_slug = str(child_spec.get("slug", "")).strip()
                child_label = str(child_spec.get("label", "")).strip()
                resolved_filter = resolve_filter(child_label, child_slug)
                resolved_label = child_label or self._slug_to_label(child_slug)
                if not resolved_filter:
                    continue
                resolved_children.append(
                    {
                        "label": resolved_label,
                        "filter": resolved_filter,
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

    def fetch_mods(self, filter_key: str = "latest", page: int = 0) -> list[dict[str, object]]:
        """Fetch FS25.NET mod cards for a specific filter and page."""
        if not filter_key:
            filter_key = self.DEFAULT_FILTER

        url = self._filter_to_url(filter_key, page)

        with self._build_session() as session:
            try:
                response = session.get(url, timeout=20)
                response.raise_for_status()
            except Exception:
                return []

        soup = BeautifulSoup(response.text, "html.parser")

        mods: list[dict[str, object]] = []
        seen: set[str] = set()

        # FS25.NET listing: <article> elements, one per mod.
        # Mod detail URLs are root-level slugs: https://fs25.net/<slug>/
        # Thumbnails are served from files.fs25.net/mods/...
        for article in soup.select("article"):
            # Primary link - first <a> inside article heading or the article itself
            link_el = article.select_one("h2 a, h3 a, .entry-title a, a[rel='bookmark']")
            if not link_el:
                link_el = article.select_one("a[href]")
            if not link_el:
                continue

            href = str(link_el.get("href", "")).strip()
            if not href:
                continue

            details_url = urljoin(self.BASE_URL, href)

            # Must be on fs25.net and NOT a category/tag/page URL
            if not details_url.startswith(self.BASE_URL):
                continue
            parsed_href = urlparse(details_url)
            path_parts = [p for p in parsed_href.path.strip("/").split("/") if p]
            if not path_parts or len(path_parts) != 1:
                continue
            if any(skip in details_url for skip in ["/category/", "/tag/", "#", "/page/"]):
                continue

            mod_id = path_parts[0]
            if mod_id in seen:
                continue

            # Title from heading inside article
            title_el = article.select_one("h2, h3, .entry-title")
            title = title_el.get_text(strip=True) if title_el else self._slug_to_label(mod_id)

            # Thumbnail — prefer files.fs25.net, fallback to any img
            thumb_url = ""
            for img in article.select("img"):
                src = str(img.get("src") or img.get("data-src") or "").strip()
                if not src:
                    continue
                if "files.fs25.net" in src or src.endswith((".webp", ".jpg", ".jpeg", ".png")):
                    thumb_url = urljoin(self.BASE_URL, src)
                    break

            if not thumb_url:
                continue

            category_name = self._extract_category_name(filter_key)

            mods.append(
                {
                    "id": mod_id,
                    "title": title,
                    "author": "FS25.NET",
                    "category": category_name,
                    "details_url": details_url,
                    "thumbnail_url": thumb_url,
                }
            )
            seen.add(mod_id)

        return mods

    def fetch_mod_details(self, details_url: str) -> dict[str, object]:
        """Fetch detailed mod information from a mod page."""
        try:
            with self._build_session() as session:
                response = session.get(details_url, timeout=20)
                response.raise_for_status()
        except Exception:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")

        # Title from h1
        title_el = soup.select_one("h1.entry-title, h1")
        title = title_el.get_text(strip=True) if title_el else "Unknown"

        # Thumbnail: prefer full-size webp from files.fs25.net
        thumbnail_url = ""
        for img in soup.select("img"):
            src = str(img.get("src") or "").strip()
            if "files.fs25.net" in src and src.endswith((".webp", ".jpg", ".jpeg", ".png")):
                thumbnail_url = src
                break

        # Description: entry-content or first substantial block
        description = "No description available."
        content_el = soup.select_one(".entry-content, [class*='entry-content'], article")
        if content_el:
            # Remove sidebar/comment sections in-place clone
            for aside in content_el.select(".widget-area, .comments-area, nav"):
                aside.decompose()
            text = content_el.get_text(" ", strip=True)
            if len(text) > 30:
                description = text[:2000]

        # Author from .author or byline
        author = "FS25.NET"
        author_el = soup.select_one(".author a, .entry-author, [rel='author']")
        if author_el:
            author = author_el.get_text(strip=True) or "FS25.NET"

        # Version extracted from title (e.g. "V1.4.0.1")
        version = ""
        ver_match = re.search(r"[Vv](\d+[\d.]+)", title)
        if ver_match:
            version = ver_match.group(1)

        # Published date
        released = ""
        time_el = soup.select_one("time[datetime], .entry-date, .published")
        if time_el:
            released = (time_el.get("datetime") or time_el.get_text(strip=True) or "")[:10]

        # Filename from download table (e.g., "zip FS25_Mercedes_Benz_G65_AMG")
        filename = ""
        for cell in soup.select("td, th"):
            text = cell.get_text(strip=True)
            if text.startswith(("zip ", "ZIP ")) or text.endswith((".zip", ".rar")):
                filename = text.lstrip("zip ").lstrip("ZIP ").strip()
                if not filename.lower().endswith((".zip", ".rar")):
                    filename += ".zip"
                break

        # Download link — direct .zip first, then any button/link near Download section
        download_url = ""
        for a in soup.select("a[href]"):
            href = str(a.get("href", "")).strip()
            if href.lower().endswith(".zip") or href.lower().endswith(".rar"):
                download_url = href
                break
        if not download_url:
            # Look for a download button or modsfire / external host link near the download block
            for a in soup.select("a[href*='modsfire'], a[href*='fboom'], a[href*='download']"):
                href = str(a.get("href", "")).strip()
                if href and not href.startswith("#"):
                    download_url = href
                    break

        return {
            "title": title,
            "description": description,
            "author": author,
            "version": version,
            "released": released,
            "filename": filename,
            "download_url": download_url,
        }

    def download_mod(
        self,
        download_url: str,
        target_dir: str,
        referer_url: str = "",
        filename: str = "",
    ) -> str:
        """Download a mod file to target_dir."""
        if not download_url:
            raise ValueError("Download URL is empty")

        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        # If no filename, try to extract from URL or generate one
        if not filename:
            parsed = urlparse(download_url)
            filename = Path(parsed.path).name or "mod.zip"

        file_path = target_path / filename
        part_path = target_path / f"{filename}.part"

        try:
            with self._build_session() as session:
                headers = {}
                if referer_url:
                    headers["Referer"] = referer_url

                response = session.get(download_url, headers=headers or None, timeout=30, stream=True)
                response.raise_for_status()

                with open(part_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                part_path.rename(file_path)
                return str(file_path)
        except Exception as exc:
            if part_path.exists():
                part_path.unlink()
            raise exc

    def fetch_category_tree(self) -> list[dict[str, object]]:
        """Return requested category tree plus extra categories discovered on FS25.NET."""
        try:
            with self._build_session() as session:
                response = session.get(self.CATEGORIES_URL, timeout=20)
                response.raise_for_status()
        except Exception:
            return self._build_requested_tree({})

        soup = BeautifulSoup(response.text, "html.parser")
        lookup = self._extract_categories_lookup(soup)
        requested_tree = self._build_requested_tree(lookup)

        # For now, just return the requested tree
        # Future enhancement: could add auto-discovered extras like KingMods does
        return requested_tree

    def fetch_category_filters(self) -> list[dict[str, str]]:
        """Flatten category tree into a flat list of filters."""
        flat: list[dict[str, str]] = []

        for node in self.fetch_category_tree():
            label = str(node.get("label", "")).strip()
            filter_key = str(node.get("filter", "")).strip()
            children = node.get("children", [])

            # Add parent if it has a filter
            if filter_key:
                flat.append({"label": label, "filter": filter_key})

            # Add children
            if isinstance(children, list):
                for child in children:
                    child_label = str(child.get("label", "")).strip()
                    child_filter = str(child.get("filter", "")).strip()
                    if child_label and child_filter:
                        flat.append({"label": child_label, "filter": child_filter})

        return flat
