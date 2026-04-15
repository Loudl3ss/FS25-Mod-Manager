"""Shared layout helpers for UI pages."""
from __future__ import annotations


def save_slot_grid_position(slot: int, rows_per_column: int = 7, max_columns: int = 3) -> tuple[int, int]:
    """Map a 1-based save slot index to a (row, column) grid position."""
    slot_index = max(slot - 1, 0)
    column = min(slot_index // rows_per_column, max_columns - 1)
    row = slot_index % rows_per_column
    return row, column
