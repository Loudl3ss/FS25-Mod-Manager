"""Shared widget style helpers for UI state updates."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget


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
