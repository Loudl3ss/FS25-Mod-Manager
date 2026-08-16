"""Save game management page."""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.game_launcher import GameLauncher
from core.save_manager import BackupInfo, SaveInfo, SaveManager
from ui.assets import Icons
from ui.widgets import HSeparator, SaveCard, StatCard


class SavesPage(QWidget):
    def __init__(self, manager: SaveManager, parent=None):
        super().__init__(parent)
        self._manager = manager
        self._build_ui()
        self._load_saves()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        ttl_col = QVBoxLayout()
        ttl_col.setSpacing(2)

        ttl_row = QHBoxLayout()
        ttl_row.setSpacing(8)
        ttl_icon = QLabel()
        ttl_icon.setPixmap(Icons.get_qicon(Icons.SAVE).pixmap(22, 22))
        ttl_row.addWidget(ttl_icon)

        ttl = QLabel("Save Manager")
        ttl.setObjectName("PageTitle")
        ttl_row.addWidget(ttl)
        ttl_row.addStretch(1)
        ttl_col.addLayout(ttl_row)

        sub = QLabel("Backup, restore and manage your save games")
        sub.setObjectName("PageSubtitle")
        ttl_col.addWidget(sub)
        hdr.addLayout(ttl_col, stretch=1)

        self._btn_launch_game = QPushButton("Launch Game")
        self._btn_launch_game.setObjectName("LaunchBtn")
        self._btn_launch_game.clicked.connect(self._launch_game)
        hdr.addWidget(self._btn_launch_game, alignment=Qt.AlignmentFlag.AlignTop)

        root.addLayout(hdr)

        # Stats row
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)
        self._stat_saves = StatCard("Active Saves", "…", "🌾", "card_saves")
        self._stat_backups = StatCard("Backups", "…", "📦", "card_backups")
        for w in [self._stat_saves, self._stat_backups]:
            stat_row.addWidget(w)
        stat_row.addStretch()
        root.addLayout(stat_row)

        root.addWidget(HSeparator())

        # ── Bulk action bar ──────────────────────────────────────────────────
        bulk_row = QHBoxLayout()
        bulk_row.setSpacing(8)

        self._btn_select_all = QPushButton("Select all")
        self._btn_select_all.setObjectName("ToolBtn")
        self._btn_select_all.clicked.connect(self._toggle_select_all)
        bulk_row.addWidget(self._btn_select_all)

        self._lbl_selection = QLabel("Nothing selected")
        self._lbl_selection.setObjectName("ModMeta")
        bulk_row.addWidget(self._lbl_selection)
        bulk_row.addStretch()

        self._btn_bulk_backup = QPushButton("Backup selected")
        self._btn_bulk_backup.setObjectName("ToolBtn")
        self._btn_bulk_backup.clicked.connect(self._bulk_backup)
        bulk_row.addWidget(self._btn_bulk_backup)

        self._btn_bulk_delete = QPushButton("Delete selected")
        self._btn_bulk_delete.setObjectName("DangerBtn")
        self._btn_bulk_delete.clicked.connect(self._bulk_delete)
        bulk_row.addWidget(self._btn_bulk_delete)

        root.addLayout(bulk_row)

        # Scroll list of save cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(2, 4, 2, 4)
        self._grid.setHorizontalSpacing(0)
        self._grid.setVerticalSpacing(6)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._grid.setColumnStretch(0, 1)

        scroll.setWidget(self._container)
        root.addWidget(scroll, stretch=1)

    # ── Load ──────────────────────────────────────────────────────────────────
    def _load_saves(self):
        # Clear old cards
        while self._grid.count() > 0:
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        saves = self._manager.get_all_saves()
        active = sum(1 for s in saves if s.exists)
        self._stat_saves.set_value(str(active))

        total_backups = len(self._manager.get_backups())
        self._stat_backups.set_value(str(total_backups))

        self._cards = []
        for index, save in enumerate(saves):
            card = SaveCard(save)
            card.backup_requested.connect(self._backup_save)
            card.restore_requested.connect(self._show_restore_dialog)
            card.delete_requested.connect(self._delete_save)
            card.copy_requested.connect(self._copy_save)
            card.selection_changed.connect(self._update_selection_state)
            # Single column list, in slot order.
            self._grid.addWidget(card, index, 0)
            self._cards.append(card)
        self._update_selection_state()

    # ── Bulk actions ──────────────────────────────────────────────────────────
    def _selected_saves(self) -> list[SaveInfo]:
        return [c.save_info for c in getattr(self, "_cards", []) if c.is_checked()]

    def _selectable_cards(self):
        return [c for c in getattr(self, "_cards", []) if c.save_info.exists]

    def _update_selection_state(self):
        count = len(self._selected_saves())
        selectable = len(self._selectable_cards())
        self._lbl_selection.setText(
            "Nothing selected" if count == 0 else f"{count} of {selectable} selected"
        )
        self._btn_bulk_backup.setEnabled(count > 0)
        self._btn_bulk_delete.setEnabled(count > 0)
        self._btn_select_all.setEnabled(selectable > 0)
        self._btn_select_all.setText(
            "Clear selection" if count and count == selectable else "Select all"
        )

    def _toggle_select_all(self):
        cards = self._selectable_cards()
        select = len(self._selected_saves()) != len(cards)
        for card in cards:
            card.set_checked(select)
        self._update_selection_state()

    def _bulk_backup(self):
        saves = self._selected_saves()
        if not saves:
            return
        done, failed = [], []
        for save in saves:
            ok, _ = self._manager.backup_save(save.slot)
            (done if ok else failed).append(save.slot)

        self._load_saves()
        summary = f"Backed up {len(done)} save(s)."
        if failed:
            summary += f"\nFailed for slot(s): {', '.join(str(s) for s in failed)}"
        QMessageBox.information(self, "Backup", summary)

    def _bulk_delete(self):
        saves = self._selected_saves()
        if not saves:
            return
        slots = ", ".join(str(s.slot) for s in saves)
        reply = QMessageBox.question(
            self,
            "Delete saves",
            f"Delete {len(saves)} save(s) permanently?\n\nSlots: {slots}\n\n"
            "This cannot be undone. Back them up first if unsure.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        done, failed = [], []
        for save in saves:
            ok, _ = self._manager.delete_save(save.slot)
            (done if ok else failed).append(save.slot)

        self._load_saves()
        summary = f"Deleted {len(done)} save(s)."
        if failed:
            summary += f"\nFailed for slot(s): {', '.join(str(s) for s in failed)}"
        QMessageBox.information(self, "Delete", summary)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _backup_save(self, save: SaveInfo):
        ok, result = self._manager.backup_save(save.slot)
        if ok:
            QMessageBox.information(
                self, "Backup Created",
                f"Backup saved to:\n{result}",
            )
            self._load_saves()
        else:
            QMessageBox.warning(self, "Backup Failed", result)

    def _show_restore_dialog(self, save: SaveInfo):
        backups = self._manager.get_backups(save.slot)
        if not backups:
            QMessageBox.information(
                self, "No Backups",
                f"No backups found for Slot {save.slot}.",
            )
            return
        dlg = BackupRestoreDialog(save, backups, self._manager, self)
        dlg.exec()
        self._load_saves()

    def _delete_save(self, save: SaveInfo):
        reply = QMessageBox.question(
            self, "Delete Save",
            f"Permanently delete Save Slot {save.slot} '{save.farm_name}'?\n"
            "This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = self._manager.delete_save(save.slot)
            if ok:
                self._load_saves()
            else:
                QMessageBox.warning(self, "Delete Failed", msg)

    def _copy_save(self, save: SaveInfo):
        available_slots: list[int] = []
        for slot in range(1, self._manager.MAX_SLOTS + 1):
            if slot == save.slot:
                continue
            slot_dir = os.path.join(self._manager.base_path, f"savegame{slot}")
            career_xml = os.path.join(slot_dir, "careerSavegame.xml")
            if not os.path.isfile(career_xml):
                available_slots.append(slot)

        if not available_slots:
            QMessageBox.information(
                self, "No Empty Slots",
                "All save slots with a valid careerSavegame.xml are occupied."
                " Delete or clear one first to make room.",
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Copy Slot {save.slot} — Select Destination")
        dlg.setMinimumSize(320, 240)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        lbl = QLabel(f"Copy <b>{save.farm_name}</b> (Slot {save.slot}) to:")
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(lbl)

        lst = QListWidget()
        for slot in available_slots:
            lst.addItem(QListWidgetItem(f"Slot {slot} — Available"))
        lst.setCurrentRow(0)
        lay.addWidget(lst, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_copy = QPushButton("Copy")
        btn_copy.setObjectName("PrimaryBtn")
        btn_copy.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_copy)

        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cancel)

        lay.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        row = lst.currentRow()
        if row < 0:
            return
        dst_slot = available_slots[row]

        ok, msg = self._manager.copy_save(save.slot, dst_slot)
        if ok:
            QMessageBox.information(
                self, "Copy Complete",
                f"Slot {save.slot} copied to Slot {dst_slot}.",
            )
            self._load_saves()
        else:
            QMessageBox.warning(self, "Copy Failed", msg)

    def _launch_game(self):
        ok, message = GameLauncher.launch_steam_game()
        if not ok:
            QMessageBox.warning(self, "Launch Failed", message)


# ─────────────────────────────────────────────────────────────────────────────
# Backup / Restore Dialog
# ─────────────────────────────────────────────────────────────────────────────
class BackupRestoreDialog(QDialog):
    def __init__(self, save: SaveInfo, backups: list[BackupInfo],
                 manager: SaveManager, parent=None):
        super().__init__(parent)
        self._save = save
        self._backups = list(backups)
        self._manager = manager

        self.setWindowTitle(f"Backups — Slot {save.slot}")
        self.setMinimumSize(520, 360)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        title = QLabel(f"Backups for Slot {save.slot} · {save.farm_name}")
        title.setObjectName("PageTitle")
        title.setStyleSheet("font-size: 16px;")
        lay.addWidget(title)

        self._list = QListWidget()
        for bp in backups:
            item = QListWidgetItem(bp.display_name)
            item.setData(Qt.ItemDataRole.UserRole, bp.path)
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        lay.addWidget(self._list, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_restore = QPushButton("🔄 Restore Selected")
        btn_restore.setObjectName("PrimaryBtn")
        btn_restore.clicked.connect(self._restore)
        btn_row.addWidget(btn_restore)

        btn_delete = QPushButton("🗑 Delete Backup")
        btn_delete.setObjectName("DangerBtn")
        btn_delete.clicked.connect(self._delete)
        btn_row.addWidget(btn_delete)

        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        lay.addLayout(btn_row)

    def _selected_path(self) -> str | None:
        item = self._list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _restore(self):
        path = self._selected_path()
        if not path:
            return
        reply = QMessageBox.question(
            self, "Confirm Restore",
            f"Restore this backup to Slot {self._save.slot}?\n"
            "Current save data will be overwritten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = self._manager.restore_save(path, self._save.slot)
            if ok:
                QMessageBox.information(self, "Restored", "Save restored successfully.")
                self.accept()
            else:
                QMessageBox.warning(self, "Failed", msg)

    def _delete(self):
        path = self._selected_path()
        if not path:
            return
        reply = QMessageBox.question(
            self, "Delete Backup",
            f"Delete backup:\n{os.path.basename(path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._manager.delete_backup(path):
                row = self._list.currentRow()
                self._list.takeItem(row)
                self._backups.pop(row)
