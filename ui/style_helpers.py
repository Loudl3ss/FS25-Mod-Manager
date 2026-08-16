"""Shared widget style helpers for UI state updates."""
from __future__ import annotations

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def refresh_widget_style(widget: QWidget) -> None:
    """Refresh style after dynamic property/state changes."""
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)


def set_bool_property(widget: QWidget, key: str, enabled: bool) -> None:
    """Set a dynamic bool-like property using QSS-friendly string values."""
    widget.setProperty(key, "true" if enabled else "false")
    refresh_widget_style(widget)


def apply_card_shadow(widget: QWidget, *, blur: int = 24, y: int = 6, alpha: int = 110) -> None:
    """Soft shadow that lifts a card off the background.

    Qt stylesheets have no box-shadow, so depth has to be applied per widget.
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)
