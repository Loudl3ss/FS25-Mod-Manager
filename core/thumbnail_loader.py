"""Shared thumbnail decoding and in-memory pixmap caching."""

from __future__ import annotations

import hashlib
from io import BytesIO

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QPixmapCache

from core.logging_utils import get_logger


logger = get_logger("thumbnail_loader")


class ThumbnailLoader:
    """Decode mod icon bytes once and reuse pixmaps from QPixmapCache."""

    _logged_failures: set[str] = set()

    @classmethod
    def obtain_local_pixmap(
        cls,
        icon_data: bytes | None,
        *,
        mod_id: str = "",
        thumbnail_id: str = "",
    ) -> QPixmap:
        if not icon_data:
            return QPixmap()

        cache_key = cls._cache_key(icon_data, mod_id=mod_id, thumbnail_id=thumbnail_id)
        cached = QPixmapCache.find(cache_key)
        if cached is not None and not cached.isNull():
            return cached

        pixmap = cls._decode_pixmap(icon_data, mod_id=mod_id, thumbnail_id=thumbnail_id)
        if not pixmap.isNull():
            QPixmapCache.insert(cache_key, pixmap)
        return pixmap

    @classmethod
    def obtain_scaled_pixmap(
        cls,
        base_pixmap: QPixmap,
        *,
        width: int,
        height: int,
        keep_aspect_by_expanding: bool = True,
    ) -> QPixmap:
        if base_pixmap.isNull() or width <= 0 or height <= 0:
            return QPixmap()

        aspect_mode = (
            Qt.AspectRatioMode.KeepAspectRatioByExpanding
            if keep_aspect_by_expanding
            else Qt.AspectRatioMode.KeepAspectRatio
        )
        cache_key = f"scaled:{base_pixmap.cacheKey()}:{width}x{height}:{int(keep_aspect_by_expanding)}"
        cached = QPixmapCache.find(cache_key)
        if cached is not None and not cached.isNull():
            return cached

        scaled = base_pixmap.scaled(
            width,
            height,
            aspect_mode,
            Qt.TransformationMode.SmoothTransformation,
        )
        if not scaled.isNull():
            QPixmapCache.insert(cache_key, scaled)
        return scaled

    @staticmethod
    def _cache_key(icon_data: bytes, *, mod_id: str, thumbnail_id: str) -> str:
        stable_id = thumbnail_id or mod_id or hashlib.sha1(icon_data).hexdigest()[:24]
        return f"thumbnail:{stable_id}"

    @classmethod
    def _decode_pixmap(cls, icon_data: bytes, *, mod_id: str, thumbnail_id: str) -> QPixmap:
        # Fast path: Qt native decode
        pixmap = QPixmap()
        if pixmap.loadFromData(icon_data) and not pixmap.isNull():
            return pixmap

        # Fallback: PIL decode (handles DDS and other exotic formats)
        try:
            from PIL import Image, UnidentifiedImageError  # pyright: ignore[reportMissingImports]
            from PIL.ImageQt import ImageQt  # pyright: ignore[reportMissingImports]

            try:
                image = Image.open(BytesIO(icon_data)).convert("RGBA")
            except UnidentifiedImageError as exc:
                cls._log_failure(mod_id, thumbnail_id, icon_data, exc)
                return cls._placeholder_pixmap()

            result = QPixmap.fromImage(QImage(ImageQt(image)))
            if not result.isNull():
                return result
        except Exception as exc:
            cls._log_failure(mod_id, thumbnail_id, icon_data, exc)

        return cls._placeholder_pixmap()

    @classmethod
    def _log_failure(cls, mod_id: str, thumbnail_id: str, icon_data: bytes, exc: Exception) -> None:
        failure_key = thumbnail_id or mod_id or hashlib.sha1(icon_data).hexdigest()[:24]
        if failure_key not in cls._logged_failures:
            cls._logged_failures.add(failure_key)
            logger.warning(
                "Failed to decode thumbnail mod_id=%s thumbnail_id=%s: %s",
                mod_id or "<unknown>",
                thumbnail_id or "<none>",
                exc,
            )

    @staticmethod
    def _placeholder_pixmap() -> QPixmap:
        from ui.assets import Icons

        icon = Icons.get_qicon(Icons.PACKAGE)
        pix = icon.pixmap(128, 128)
        return pix if not pix.isNull() else QPixmap()