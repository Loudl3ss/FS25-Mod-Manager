"""Shared logging helpers for FS25 Manager core modules."""

from __future__ import annotations

import logging


ROOT_LOGGER_NAME = "fs25_manager"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced logger under the application root logger."""
    root = logging.getLogger(ROOT_LOGGER_NAME)
    if not root.handlers:
        root.addHandler(logging.NullHandler())

    if not name:
        return root
    return root.getChild(name)