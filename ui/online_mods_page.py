"""Online mods browser page using threaded scraping worker."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from typing import Any, Callable

from PyQt6.QtCore import QPoint, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.logging_utils import get_logger
from core.online_scraper import FarmingSimulatorScraper
from core.online_thumbnail_cache import OnlineThumbnailCache
from ui.mod_grid import ModCard, ResponsiveModGrid
from ui.network_helpers import build_retry_session
from ui.style_helpers import refresh_widget_style, set_bool_property

import requests


logger = get_logger("ui.online_mods")


class HoverCategoryButton(QPushButton):
    hovered = pyqtSignal()
    hover_changed = pyqtSignal(bool)

    def enterEvent(self, event):
        self.hovered.emit()
        self.hover_changed.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):  # type: ignore[override]
        self.hover_changed.emit(False)
        super().leaveEvent(event)


class ScraperWorker(QThread):
    """Background worker to keep UI responsive during fetch."""

    finished_data = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, page: int, filter_key: str, scraper_factory: Callable[[], Any]):
        super().__init__()
        self._page = page
        self._filter_key = filter_key
        self._scraper = scraper_factory()
        self._thumb_cache = OnlineThumbnailCache()
        self._session = build_retry_session(user_agent="FS25-Mod-Manager/OnlineScraper")

    def _fetch_thumbnail_bytes(self, thumb_url: str, referer_url: str = "") -> bytes:
        cached = self._thumb_cache.get(thumb_url)
        if cached:
            return cached

        try:
            headers = {"Referer": referer_url or "https://www.farming-simulator.com/"}
            response = self._session.get(thumb_url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.content
            if data:
                self._thumb_cache.set(thumb_url, data)
            return data
        except requests.RequestException:
            return b""

    def run(self):
        try:
            data = self._scraper.fetch_mods(filter_key=self._filter_key, page=self._page)

            jobs = []
            for idx, mod in enumerate(data):
                thumb_url = str(mod.get("thumbnail_url", "")).strip()
                referer_url = str(mod.get("details_url", "")).strip()
                mod["thumbnail_data"] = b""
                if thumb_url:
                    jobs.append((idx, thumb_url, referer_url))

            with ThreadPoolExecutor(max_workers=6) as executor:
                future_to_index = {
                    executor.submit(self._fetch_thumbnail_bytes, url, referer): idx
                    for idx, url, referer in jobs
                }
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    thumb_data = future.result()
                    data[idx]["thumbnail_data"] = thumb_data

            self.finished_data.emit(data)
        except Exception as exc:  # pragma: no cover - defensive UI path
            logger.warning("ScraperWorker failed page=%s filter=%s: %s", self._page, self._filter_key, exc)
            self.error_occurred.emit(str(exc))
        finally:
            self._session.close()


class ModDetailWorker(QThread):
    finished_details = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, mod_id: str, details_url: str, scraper_factory: Callable[[], Any]):
        super().__init__()
        self._mod_id = mod_id
        self._details_url = details_url
        self._scraper = scraper_factory()

    def run(self):
        try:
            details = self._scraper.fetch_mod_details(self._details_url)
            details["id"] = self._mod_id
            self.finished_details.emit(details)
        except Exception as exc:  # pragma: no cover - defensive UI path
            logger.warning("ModDetailWorker failed mod_id=%s url=%s: %s", self._mod_id, self._details_url, exc)
            self.error_occurred.emit(str(exc))


class ModDownloadWorker(QThread):
    finished_download = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        download_url: str,
        target_dir: str,
        referer_url: str,
        filename: str,
        scraper_factory: Callable[[], Any],
    ):
        super().__init__()
        self._download_url = download_url
        self._target_dir = target_dir
        self._referer_url = referer_url
        self._filename = filename
        self._scraper = scraper_factory()

    def run(self):
        try:
            saved_path = self._scraper.download_mod(
                self._download_url,
                self._target_dir,
                referer_url=self._referer_url,
                filename=self._filename,
            )
            self.finished_download.emit(saved_path)
        except Exception as exc:  # pragma: no cover - defensive UI path
            logger.warning(
                "ModDownloadWorker failed url=%s target_dir=%s filename=%s: %s",
                self._download_url,
                self._target_dir,
                self._filename,
                exc,
            )
            self.error_occurred.emit(str(exc))


class OnlineModDetailPanel(QWidget):
    download_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mod: dict[str, object] | None = None
        self.setMinimumWidth(320)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        self._thumb_frame = QFrame()
        self._thumb_frame.setFixedSize(180, 180)
        self._thumb_frame.setStyleSheet(
            "background: #1e293b; border-radius: 12px;"
        )
        _thumb_inner = QVBoxLayout(self._thumb_frame)
        _thumb_inner.setContentsMargins(5, 5, 5, 5)
        _thumb_inner.setSpacing(0)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet(
            "background: transparent; border-radius: 8px; font-size: 48px;"
        )
        _thumb_inner.addWidget(self._icon_lbl)
        lay.addWidget(self._thumb_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._title_lbl = QLabel()
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_lbl.setObjectName("ModTitle")
        lay.addWidget(self._title_lbl)

        self._meta_lbl = QLabel()
        self._meta_lbl.setWordWrap(True)
        self._meta_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._meta_lbl)

        self._desc_edit = QTextEdit()
        self._desc_edit.setReadOnly(True)
        self._desc_edit.setMinimumHeight(220)
        lay.addWidget(self._desc_edit, stretch=1)

        self._download_btn = QPushButton("Download")
        self._download_btn.setObjectName("PrimaryBtn")
        self._download_btn.setFixedSize(140, 36)
        self._download_btn.clicked.connect(self._on_download_clicked)
        self._download_btn.hide()
        lay.addWidget(self._download_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.clear()

    def clear(self):
        self._current_mod = None
        self._icon_lbl.setText("🌾")
        self._icon_lbl.setPixmap(QPixmap())
        self._title_lbl.setText("Select an FS25 mod")
        self._meta_lbl.setText("")
        self._desc_edit.setPlainText("Click a mod card to load details here.")
        self._download_btn.hide()
        self._download_btn.setEnabled(True)
        self._download_btn.setText("Download")

    def show_loading(self, mod: dict[str, object], thumbnail: QPixmap):
        self._current_mod = mod
        if not thumbnail.isNull():
            self._icon_lbl.setPixmap(
                thumbnail.scaled(
                    170,
                    170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self._icon_lbl.setText("")
        else:
            self._icon_lbl.setPixmap(QPixmap())
            self._icon_lbl.setText("🌾")

        self._title_lbl.setText(str(mod.get("title", "Unknown")))
        self._meta_lbl.setText(f"Author: {mod.get('author', '')}\nCategory: {mod.get('category', '')}")
        self._desc_edit.setPlainText("Loading full mod details...")
        self._download_btn.hide()

    def show_details(self, details: dict[str, object], thumbnail: QPixmap):
        merged = dict(self._current_mod or {})
        merged.update(details)
        self._current_mod = merged

        if not thumbnail.isNull():
            self._icon_lbl.setPixmap(
                thumbnail.scaled(
                    170,
                    170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self._icon_lbl.setText("")
        else:
            self._icon_lbl.setPixmap(QPixmap())
            self._icon_lbl.setText("🌾")

        self._title_lbl.setText(str(merged.get("title", "Unknown")))
        meta_parts = []
        for label, key in [
            ("Author", "author"),
            ("Category", "category"),
            ("Filename", "filename"),
            ("Size", "size"),
            ("Version", "version"),
            ("Released", "released"),
            ("Platform", "platform"),
            ("Rating", "rating"),
        ]:
            value = str(merged.get(key, "")).strip()
            if value:
                meta_parts.append(f"{label}: {value}")
        self._meta_lbl.setText("\n".join(meta_parts))
        self._desc_edit.setPlainText(str(merged.get("description", "No description available.")))

        has_download = bool(str(merged.get("download_url", "")).strip())
        self._download_btn.setVisible(has_download)
        self._download_btn.setEnabled(True)
        self._download_btn.setText("Download")

    def set_download_in_progress(self):
        self._download_btn.setVisible(True)
        self._download_btn.setEnabled(False)
        self._download_btn.setText("Downloading...")

    def _on_download_clicked(self):
        if self._current_mod is None:
            return
        mod_id = str(self._current_mod.get("id", "")).strip()
        if mod_id:
            self.download_requested.emit(mod_id)


class OnlineModsPage(QWidget):
    """Online FS25 view with subcategory navigation and threaded fetch."""

    def __init__(
        self,
        mods_path: str,
        parent=None,
        scraper_factory: Callable[[], Any] | None = None,
        page_title: str = "Official FS25 Mods",
        page_subtitle: str = "Browse all FS25 ModHub categories",
        default_filter: str = "latest",
        default_filter_label: str = "Latest",
    ):
        super().__init__(parent)
        self._mods_path = mods_path
        self._scraper_factory = scraper_factory or FarmingSimulatorScraper
        self._page_title = page_title
        self._page_subtitle = page_subtitle
        self._worker: ScraperWorker | None = None
        self._detail_worker: ModDetailWorker | None = None
        self._download_worker: ModDownloadWorker | None = None
        self._category_worker: CategoryWorker | None = None
        self._next_page = 0
        self._current_page = 0
        self._current_filter = default_filter
        self._current_filter_label = default_filter_label
        self._append_mode = False
        self._seen_mod_ids: set[str] = set()
        self._mods_by_id: dict[str, dict[str, object]] = {}
        self._cards_by_id: dict[str, ModCard] = {}
        self._selected_card = None
        self._selected_mod_id: str | None = None
        self._category_buttons: list[HoverCategoryButton] = []
        self._category_button_meta: dict[HoverCategoryButton, dict[str, object]] = {}
        self._category_popup_menus: dict[HoverCategoryButton, QMenu] = {}
        self._submenu_actions: dict[str, QAction] = {}
        self._active_popup_menu: QMenu | None = None
        self._load_all_active = False
        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Main content area (left)
        content = QWidget()
        latest_layout = QVBoxLayout(content)
        latest_layout.setContentsMargins(24, 20, 24, 20)
        latest_layout.setSpacing(12)

        title = QLabel(self._page_title)
        title.setObjectName("PageTitle")
        latest_layout.addWidget(title)
        self.title_label = title

        subtitle = QLabel(self._page_subtitle)
        subtitle.setObjectName("PageSubtitle")
        latest_layout.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.btn_refresh = QPushButton("Refresh/Fetch")
        self.btn_refresh.setObjectName("ToolBtn")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        actions.addWidget(self.btn_refresh)

        self.btn_load_more = QPushButton("Load More")
        self.btn_load_more.setObjectName("ToolBtn")
        self.btn_load_more.clicked.connect(self._on_load_more_clicked)
        actions.addWidget(self.btn_load_more)

        self.btn_load_all = QPushButton("Load All")
        self.btn_load_all.setObjectName("ToolBtn")
        self.btn_load_all.clicked.connect(self._on_load_all_clicked)
        actions.addWidget(self.btn_load_all)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search mods...")
        self.search_bar.setFixedWidth(220)
        self.search_bar.setFixedHeight(30)
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setStyleSheet(
            "QLineEdit { background: #1e293b; color: #e2e8f0; border: 1px solid #334155;"
            " border-radius: 6px; padding: 2px 8px; font-size: 13px; }"
            "QLineEdit:focus { border: 1px solid #4ade80; }"
        )
        self.search_bar.textChanged.connect(self._on_search_changed)
        actions.addWidget(self.search_bar, alignment=Qt.AlignmentFlag.AlignVCenter)
        actions.addStretch(1)

        latest_layout.addLayout(actions)

        self.status_label = QLabel("Press Refresh/Fetch to load placeholder data")
        latest_layout.addWidget(self.status_label)

        latest_body = QHBoxLayout()
        latest_body.setSpacing(12)

        self.results_grid = ResponsiveModGrid()
        self.results_grid.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        latest_body.addWidget(self.results_grid, stretch=1)

        self.detail_panel = OnlineModDetailPanel()
        self.detail_panel.download_requested.connect(self._on_download_requested)
        latest_body.addWidget(self.detail_panel)

        latest_layout.addLayout(latest_body, stretch=1)

        # Left category panel
        self.sub_panel = QFrame()
        self.sub_panel.setObjectName("SubSidebar")
        self.sub_panel.setFixedWidth(220)
        self.sub_panel.setStyleSheet(
            """
            QFrame#SubSidebar {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            QPushButton#SubNavBtn {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 4px 10px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 400;
                margin: 1px 8px;
                border-radius: 8px;
            }
            QPushButton#SubNavBtn:hover {
                background-color: rgba(30, 41, 59, 0.95);
                color: #e2e8f0;
            }
            QPushButton#SubNavBtn[hovered="true"],
            QPushButton#SubNavBtn[submenuOpen="true"] {
                color: #86efac;
                background-color: rgba(34, 197, 94, 0.08);
                border-left: 3px solid #4ade80;
            }
            QPushButton#SubNavBtn[active=\"true\"] {
                font-weight: 600;
                color: #4ade80;
                background-color: rgba(74, 222, 128, 0.1);
                border-left: 3px solid #4ade80;
            }
            """
        )

        panel_layout = QVBoxLayout(self.sub_panel)
        panel_layout.setContentsMargins(0, 14, 0, 0)
        panel_layout.setSpacing(2)

        cat_header = QLabel("CATEGORIES")
        cat_header.setObjectName("SidebarSection")
        cat_header.setContentsMargins(12, 0, 8, 0)
        panel_layout.addWidget(cat_header)

        self.category_scroll = QScrollArea()
        self.category_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.category_scroll.setWidgetResizable(True)
        self.category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.category_container = QWidget()
        self.category_scroll.setWidget(self.category_container)
        self.category_layout = QVBoxLayout(self.category_container)
        self.category_layout.setContentsMargins(0, 0, 0, 0)
        self.category_layout.setSpacing(2)

        self.category_status_label = QLabel("Wait ... Loading mods")
        self.category_status_label.setObjectName("PageSubtitle")
        self.category_status_label.setContentsMargins(12, 6, 8, 6)
        self.category_layout.addWidget(self.category_status_label)

        panel_layout.addWidget(self.category_scroll, stretch=1)
        panel_layout.addStretch()

        root.addWidget(self.sub_panel)

        # Keep a visible separator so popup/hover states never visually hide the panel edge.
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background-color: #1e293b;")
        root.addWidget(divider)

        root.addWidget(content, stretch=1)

    def _add_category_button(self, text: str, filter_key: str = "", children: list[dict[str, str]] | None = None):
        btn_text = f"{text}   ▶" if children else text
        btn = HoverCategoryButton(btn_text)
        btn.setObjectName("SubNavBtn")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("filter_key", filter_key)
        btn.setProperty("hovered", "false")
        btn.setProperty("submenuOpen", "false")
        btn.hover_changed.connect(lambda is_hovered, b=btn: self._set_button_state(b, "hovered", is_hovered))
        child_filters = [str(child.get("filter", "")).strip() for child in (children or []) if str(child.get("filter", "")).strip()]
        self._category_button_meta[btn] = {
            "filter": filter_key,
            "label": text,
            "child_filters": child_filters,
        }

        if children:
            menu = QMenu(self)
            menu.setObjectName("OnlineCategoryPopup")
            menu.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            menu.setStyleSheet(
                """
                QMenu#OnlineCategoryPopup {
                    background: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 6px;
                }
                QMenu#OnlineCategoryPopup::item {
                    color: #cbd5e1;
                    border-radius: 6px;
                    padding: 7px 12px;
                    min-width: 180px;
                }
                QMenu#OnlineCategoryPopup::item:selected {
                    background: rgba(30, 41, 59, 0.98);
                    color: #e2e8f0;
                }
                QMenu#OnlineCategoryPopup::item:checked {
                    background: rgba(74, 222, 128, 0.12);
                    color: #4ade80;
                }
                """
            )

            shadow = QGraphicsDropShadowEffect(menu)
            shadow.setBlurRadius(28)
            shadow.setOffset(0, 8)
            shadow.setColor(QColor(0, 0, 0, 180))
            menu.setGraphicsEffect(shadow)

            for child in children:
                child_label = str(child.get("label", "")).strip()
                child_filter = str(child.get("filter", "")).strip()
                if not child_label or not child_filter:
                    continue
                action = menu.addAction(child_label)
                if action is not None:
                    action.setCheckable(True)
                    self._submenu_actions[child_filter] = action
                    action.triggered.connect(
                        lambda checked=False, fk=child_filter, lbl=child_label: self._on_category_selected(fk, lbl)
                    )
            self._category_popup_menus[btn] = menu
            btn.hovered.connect(lambda b=btn: self._show_subcategory_popup(b))
            btn.clicked.connect(lambda checked=False, b=btn: self._show_subcategory_popup(b))
            def _on_hide(b=btn, m=menu):
                self._set_button_state(b, "submenuOpen", False)
                if self._active_popup_menu is m:
                    self._active_popup_menu = None
            menu.aboutToHide.connect(_on_hide)
        elif filter_key:
            btn.clicked.connect(lambda checked=False, fk=filter_key, t=text: self._on_category_selected(fk, t))

        self.category_layout.addWidget(btn)
        self._category_buttons.append(btn)

    def _show_subcategory_popup(self, button: HoverCategoryButton):
        menu = self._category_popup_menus.get(button)
        if menu is None:
            return
        # Close any currently open popup first to avoid Wayland transient parent crash.
        if self._active_popup_menu is not None and self._active_popup_menu is not menu:
            self._active_popup_menu.close()
            self._active_popup_menu = None
        if menu.isVisible():
            return
        self._active_popup_menu = menu
        self._set_button_state(button, "submenuOpen", True)
        # Slight overlap keeps it visually attached to the sidebar edge.
        global_pos = button.mapToGlobal(button.rect().topRight()) + QPoint(2, -2)
        menu.popup(global_pos)

    def _set_button_state(self, button: HoverCategoryButton, key: str, enabled: bool):
        set_bool_property(button, key, enabled)

    def _set_active_category(self, filter_key: str):
        for btn in self._category_buttons:
            meta = self._category_button_meta.get(btn, {})
            direct_filter = str(meta.get("filter", ""))
            raw_child_filters = meta.get("child_filters", [])
            child_filters = raw_child_filters if isinstance(raw_child_filters, list) else []
            active = direct_filter == filter_key or filter_key in child_filters
            set_bool_property(btn, "active", active)
            btn.setChecked(active)

        for child_filter, action in self._submenu_actions.items():
            action.setChecked(child_filter == filter_key)

    def _clear_category_buttons(self):
        for btn in self._category_buttons:
            menu = self._category_popup_menus.pop(btn, None)
            if menu is not None:
                menu.deleteLater()
            self.category_layout.removeWidget(btn)
            btn.deleteLater()

        self._category_buttons.clear()
        self._category_button_meta.clear()
        self._submenu_actions.clear()

    def _load_categories(self):
        if self._category_worker is not None and self._category_worker.isRunning():
            return

        self.category_status_label.setText("Wait ... Loading mods")
        self.category_status_label.show()
        self._category_worker = CategoryWorker(self._scraper_factory)
        self._category_worker.finished_categories.connect(self._on_categories_loaded)
        self._category_worker.error_occurred.connect(self._on_categories_error)
        self._category_worker.finished.connect(self._on_category_worker_finished)
        self._category_worker.start()

    def _on_category_worker_finished(self):
        if self._category_worker is not None:
            self._category_worker.deleteLater()
            self._category_worker = None

    def _on_categories_loaded(self, categories: list[dict]):
        self._clear_category_buttons()
        added = 0

        # Always keep the default entry available and first in the list.
        self._add_category_button(self._current_filter_label, self._current_filter)
        added += 1

        existing_filters = {self._current_filter}
        for category in categories:
            label = str(category.get("label", "")).strip()
            filter_key = str(category.get("filter", "")).strip()
            children = category.get("children", [])

            if children:
                self._add_category_button(label, "", children=children)
                added += 1
                continue

            if not label or not filter_key or filter_key in existing_filters:
                continue
            self._add_category_button(label, filter_key)
            existing_filters.add(filter_key)
            added += 1

        self.category_status_label.setVisible(added == 0)
        if added == 0:
            self.category_status_label.setText("No categories found")
        self._set_active_category(self._current_filter)

    def _on_categories_error(self, _message: str):
        self._clear_category_buttons()
        self.category_status_label.setText("No categories found")
        self.category_status_label.show()

    def _on_category_selected(self, filter_key: str, label: str):
        self._load_all_active = False
        self._current_filter = filter_key
        self._current_filter_label = label
        self.title_label.setText(label)
        self.search_bar.blockSignals(True)
        self.search_bar.clear()
        self.search_bar.blockSignals(False)
        self._set_active_category(filter_key)
        self._start_fetch(page=0, append=False)

    def _on_search_changed(self, text: str):
        query = text.strip().lower()
        for mod_id, card in self._cards_by_id.items():
            mod = self._mods_by_id.get(mod_id, {})
            name = str(mod.get("title", "")).lower()
            card.setVisible(not query or query in name)

    def _on_refresh_clicked(self):
        self._load_all_active = False
        self.search_bar.blockSignals(True)
        self.search_bar.clear()
        self.search_bar.blockSignals(False)
        self._start_fetch(page=0, append=False)

    def _on_load_more_clicked(self):
        self._load_all_active = False
        page_to_load = self._next_page
        self._start_fetch(page=page_to_load, append=True)

    def _on_load_all_clicked(self):
        self._load_all_active = True
        if self._seen_mod_ids:
            # Continue from where we left off
            self._start_fetch(page=self._next_page, append=True)
        else:
            # Start fresh
            self._start_fetch(page=0, append=False)

    def _start_fetch(self, page: int, append: bool):
        if self._worker is not None and self._worker.isRunning():
            return

        self._append_mode = append
        self._current_page = page
        self.btn_refresh.setEnabled(False)
        self.btn_load_more.setEnabled(False)
        self.btn_load_all.setEnabled(False)

        action = "Loading more mods" if append else "Refreshing mods"
        self.status_label.setText(f"{action} {self._current_filter_label} (page {page})...")

        self._worker = ScraperWorker(
            page=page,
            filter_key=self._current_filter,
            scraper_factory=self._scraper_factory,
        )
        self._worker.finished_data.connect(self._on_data_loaded)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._on_scraper_worker_finished)
        self._worker.start()

    def _on_scraper_worker_finished(self):
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def _on_data_loaded(self, mods: list[dict[str, object]]):
        if not self._append_mode:
            self.results_grid.clear_mods()
            self._seen_mod_ids.clear()
            self._mods_by_id.clear()
            self._cards_by_id.clear()
            self._selected_card = None
            self._selected_mod_id = None
            self.detail_panel.clear()
            self._next_page = 0

        if not mods:
            if self._load_all_active:
                self._load_all_active = False
                self.status_label.setText(
                    f"Loaded all {self._current_filter_label} mods. "
                    f"Total: {len(self._seen_mod_ids)}"
                )
            elif self._append_mode:
                self.status_label.setText(f"No more mods found for {self._current_filter_label}")
            else:
                self.status_label.setText(f"No mods found for {self._current_filter_label} on page 0")
            return

        added_count = 0
        for mod in mods:
            mod_id = str(mod.get("id", "")).strip() or str(mod.get("details_url", "")).strip()
            if not mod_id or mod_id in self._seen_mod_ids:
                continue

            title = str(mod.get("title", "Unknown"))
            author = str(mod.get("author", ""))
            category = str(mod.get("category", "Unknown"))
            thumbnail = QPixmap()
            thumb_data = mod.get("thumbnail_data", b"")
            if isinstance(thumb_data, (bytes, bytearray)) and thumb_data:
                thumbnail.loadFromData(thumb_data)

            card = self.results_grid.add_mod(
                mod_id=mod_id,
                thumbnail=thumbnail,
                name=title,
                version=author,
                is_favorite=False,
                category=category,
                thumbnail_id=mod_id,
                show_favorite=False,
            )

            card.modClicked.connect(self._on_mod_clicked)

            self._seen_mod_ids.add(mod_id)
            self._mods_by_id[mod_id] = mod
            self._cards_by_id[mod_id] = card
            added_count += 1

        self._next_page = self._current_page + 1
        self.status_label.setText(
            f"Loaded {self._current_filter_label} page {self._current_page} ({added_count} new mod(s)). "
            f"Total items: {len(self._seen_mod_ids)}"
        )

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")

    def _on_worker_finished(self):
        self.btn_refresh.setEnabled(True)
        self.btn_load_more.setEnabled(True)
        self.btn_load_all.setEnabled(True)
        if self._load_all_active:
            # Check if last fetch added anything; if yes, continue to next page
            last_page_count_key = self._current_page
            # Re-use _next_page which is already incremented after a successful load
            if self._next_page > self._current_page:
                # More pages may exist — keep going
                self._start_fetch(page=self._next_page, append=True)
            else:
                # Nothing new was loaded, stop
                self._load_all_active = False
                self.status_label.setText(
                    f"Loaded all {self._current_filter_label} mods. "
                    f"Total: {len(self._seen_mod_ids)}"
                )

    def _on_mod_clicked(self, mod_id: str):
        mod = self._mods_by_id.get(mod_id)
        card = self._cards_by_id.get(mod_id)
        if mod is None or card is None:
            return

        if self._selected_card and hasattr(self._selected_card, "set_selected"):
            self._selected_card.set_selected(False)
        self._selected_card = card
        self._selected_mod_id = mod_id
        if hasattr(card, "set_selected"):
            card.set_selected(True)

        thumbnail = QPixmap()
        thumb_data = mod.get("thumbnail_data", b"")
        if isinstance(thumb_data, (bytes, bytearray)) and thumb_data:
            thumbnail.loadFromData(thumb_data)
        self.detail_panel.show_loading(mod, thumbnail)

        details_url = str(mod.get("details_url", "")).strip()
        if not details_url:
            self.detail_panel.show_details(mod, thumbnail)
            return

        self._detail_worker = ModDetailWorker(mod_id, details_url, self._scraper_factory)
        self._detail_worker.finished_details.connect(self._on_detail_loaded)
        self._detail_worker.error_occurred.connect(self._on_error)
        self._detail_worker.finished.connect(self._on_detail_worker_finished)
        self._detail_worker.start()

    def _on_detail_worker_finished(self):
        if self._detail_worker is not None:
            self._detail_worker.deleteLater()
            self._detail_worker = None

    def _on_detail_loaded(self, details: dict):
        mod_id = str(details.get("id", "")).strip()
        if not mod_id or mod_id != self._selected_mod_id:
            return

        mod = self._mods_by_id.get(mod_id, {})
        mod.update(details)
        self._mods_by_id[mod_id] = mod

        thumbnail = QPixmap()
        thumb_data = mod.get("thumbnail_data", b"")
        if isinstance(thumb_data, (bytes, bytearray)) and thumb_data:
            thumbnail.loadFromData(thumb_data)
        self.detail_panel.show_details(mod, thumbnail)

    def _on_download_requested(self, mod_id: str):
        mod = self._mods_by_id.get(mod_id)
        if mod is None:
            return

        download_url = str(mod.get("download_url", "")).strip()
        details_url = str(mod.get("details_url", "")).strip()
        filename = str(mod.get("filename", "")).strip()
        title = str(mod.get("title", "Unknown"))

        if not download_url:
            QMessageBox.warning(self, "Download Mod", "This mod does not have a download link.")
            return

        confirm_text = (
            f"Download '{title}' directly into your mods folder?\n\n"
            f"Destination: {self._mods_path}"
        )
        if filename:
            confirm_text += f"\nFile: {filename}"

        reply = QMessageBox.question(
            self,
            "Download Mod",
            confirm_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.detail_panel.set_download_in_progress()
        self.status_label.setText(f"Downloading {title}...")
        self._download_worker = ModDownloadWorker(
            download_url,
            self._mods_path,
            details_url,
            filename,
            self._scraper_factory,
        )
        self._download_worker.finished_download.connect(self._on_download_finished)
        self._download_worker.error_occurred.connect(self._on_download_error)
        self._download_worker.finished.connect(self._on_download_worker_finished)
        self._download_worker.start()

    def _on_download_worker_finished(self):
        if self._download_worker is not None:
            self._download_worker.deleteLater()
            self._download_worker = None

    def _on_download_finished(self, saved_path: str):
        self.status_label.setText(f"Downloaded mod to {saved_path}")
        if self._selected_mod_id and self._selected_mod_id in self._mods_by_id:
            mod = self._mods_by_id[self._selected_mod_id]
            thumbnail = QPixmap()
            thumb_data = mod.get("thumbnail_data", b"")
            if isinstance(thumb_data, (bytes, bytearray)) and thumb_data:
                thumbnail.loadFromData(thumb_data)
            self.detail_panel.show_details(mod, thumbnail)
        QMessageBox.information(self, "Download Complete", f"Mod saved to:\n{saved_path}")

    def _on_download_error(self, message: str):
        self.status_label.setText(f"Download failed: {message}")
        QMessageBox.warning(self, "Download Failed", message)
        if self._selected_mod_id and self._selected_mod_id in self._mods_by_id:
            mod = self._mods_by_id[self._selected_mod_id]
            thumbnail = QPixmap()
            thumb_data = mod.get("thumbnail_data", b"")
            if isinstance(thumb_data, (bytes, bytearray)) and thumb_data:
                thumbnail.loadFromData(thumb_data)
            self.detail_panel.show_details(mod, thumbnail)

    @staticmethod
    def _stop_thread(thread: QThread | None) -> None:
        if thread is None:
            return

        if thread.isRunning():
            with suppress(Exception):
                thread.requestInterruption()
            with suppress(Exception):
                thread.quit()
            with suppress(Exception):
                thread.wait(1000)
        thread.deleteLater()

    def closeEvent(self, event):  # type: ignore[override]
        self._stop_thread(self._worker)
        self._worker = None
        self._stop_thread(self._detail_worker)
        self._detail_worker = None
        self._stop_thread(self._download_worker)
        self._download_worker = None
        self._stop_thread(self._category_worker)
        self._category_worker = None
        super().closeEvent(event)


class CategoryWorker(QThread):
    finished_categories = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, scraper_factory: Callable[[], Any]):
        super().__init__()
        self._scraper = scraper_factory()

    def run(self):
        try:
            categories = self._scraper.fetch_category_tree()
            visible_categories: list[dict[str, object]] = []

            for category in categories:
                label = str(category.get("label", "")).strip()
                filter_key = str(category.get("filter", "")).strip()
                children = category.get("children", [])
                if not isinstance(children, list):
                    children = []

                if children:
                    visible_children: list[dict[str, str]] = []
                    for child in children:
                        child_filter = str(child.get("filter", "")).strip()
                        child_label = str(child.get("label", "")).strip()
                        if not child_filter or not child_label:
                            continue
                        visible_children.append(
                            {
                                "label": child_label,
                                "filter": child_filter,
                            }
                        )

                    if visible_children:
                        visible_categories.append(
                            {
                                "label": label,
                                "filter": "",
                                "children": visible_children,
                            }
                        )
                elif filter_key:
                    visible_categories.append(
                        {
                            "label": label,
                            "filter": filter_key,
                            "children": [],
                        }
                    )

            self.finished_categories.emit(visible_categories)
        except Exception as exc:  # pragma: no cover - defensive UI path
            logger.warning("CategoryWorker failed: %s", exc)
            self.error_occurred.emit(str(exc))
