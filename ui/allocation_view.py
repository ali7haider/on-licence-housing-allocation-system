"""Rank, shortlist, and allocate RHUs for licensees."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from logic.matching import rank_rhus_for
from models.person import Licensee


class AllocationView(QWidget):
    """Give the allocation officer ranked RHU options while retaining control."""

    allocation_changed = Signal()

    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create licensee selection, ranked RHUs, shortlist, and allocation controls."""
        layout = QVBoxLayout(self)

        selection_row = QHBoxLayout()
        selection_row.addWidget(QLabel("Find licensee:"))
        self.licensee_search = QLineEdit()
        self.licensee_search.setPlaceholderText("Search by name or prison role ID")
        self.licensee_search.textChanged.connect(self._populate_licensee_picker)
        selection_row.addWidget(self.licensee_search)

        self.licensee_picker = QComboBox()
        self.licensee_picker.currentIndexChanged.connect(self._rank_selected_licensee)
        selection_row.addWidget(self.licensee_picker, 2)
        layout.addLayout(selection_row)

        content = QHBoxLayout()
        table_column = QVBoxLayout()
        table_column.addWidget(QLabel("Ranked RHUs (all options remain visible)"))
        self.ranking_table = QTableWidget(0, 4)
        self.ranking_table.setHorizontalHeaderLabels(["RHU", "Score", "Cost/day", "Warnings"])
        self.ranking_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ranking_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ranking_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ranking_table.horizontalHeader().setStretchLastSection(True)
        table_column.addWidget(self.ranking_table)

        ranked_actions = QHBoxLayout()
        shortlist_button = QPushButton("Add selected to shortlist")
        shortlist_button.clicked.connect(self._add_to_shortlist)
        ranked_actions.addWidget(shortlist_button)
        allocate_button = QPushButton("Allocate selected RHU")
        allocate_button.clicked.connect(self._allocate_selected_rhu)
        ranked_actions.addWidget(allocate_button)
        table_column.addLayout(ranked_actions)
        content.addLayout(table_column, 3)

        shortlist_column = QVBoxLayout()
        shortlist_column.addWidget(QLabel("Shortlist (maximum 5)"))
        self.shortlist = QListWidget()
        shortlist_column.addWidget(self.shortlist)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self._remove_from_shortlist)
        shortlist_column.addWidget(remove_button)
        content.addLayout(shortlist_column, 1)
        layout.addLayout(content)

    def refresh(self) -> None:
        """Reload licensee choices while retaining the selected licensee where possible."""
        selected_id = self._selected_licensee_id()
        self._populate_licensee_picker(selected_id)

    def _populate_licensee_picker(self, selected_id: str | None = None) -> None:
        """Fill the picker with records matching the search text."""
        if selected_id is None:
            selected_id = self._selected_licensee_id()
        matching_licensees = self.data_store.search_licensees(self.licensee_search.text())
        matching_licensees.sort(key=lambda licensee: licensee.name.casefold())

        self.licensee_picker.blockSignals(True)
        self.licensee_picker.clear()
        self.licensee_picker.addItem("Select a licensee", None)
        for licensee in matching_licensees:
            self.licensee_picker.addItem(
                f"{licensee.name} ({licensee.prison_role_id}) — {licensee.state.value}",
                licensee.prison_role_id,
            )
        index = self.licensee_picker.findData(selected_id)
        self.licensee_picker.setCurrentIndex(index if index >= 0 else 0)
        self.licensee_picker.blockSignals(False)
        self._rank_selected_licensee()

    def _selected_licensee_id(self) -> str | None:
        """Return the role ID selected in the picker, if any."""
        value = self.licensee_picker.currentData()
        return str(value) if value is not None else None

    def _selected_licensee(self) -> Licensee | None:
        """Look up the currently selected licensee from the data store."""
        licensee_id = self._selected_licensee_id()
        return self.data_store.get_licensee(licensee_id) if licensee_id else None

    def _rank_selected_licensee(self, *_: object) -> None:
        """Populate the RHU table and shortlist for the selected licensee.

        Rebuilding the table clears Qt's row selection, so the previously
        selected RHU (if any) is restored afterwards. Without this, selecting
        a row, then adding it to the shortlist, silently deselects it and the
        next "Allocate selected RHU" click does nothing.
        """
        previously_selected_rhu = self._selected_rhu_name()
        self.ranking_table.setRowCount(0)
        self.shortlist.clear()
        licensee = self._selected_licensee()
        if licensee is None:
            return

        restore_row = -1
        for row, (rhu, score, warnings, cost) in enumerate(rank_rhus_for(licensee, self.data_store.list_rhus())):
            self.ranking_table.insertRow(row)
            name_item = QTableWidgetItem(rhu.name)
            name_item.setData(Qt.ItemDataRole.UserRole, rhu.name)
            self.ranking_table.setItem(row, 0, name_item)
            self.ranking_table.setItem(row, 1, QTableWidgetItem(str(score)))
            self.ranking_table.setItem(row, 2, QTableWidgetItem(f"£{cost:.2f}"))
            self.ranking_table.setItem(
                row,
                3,
                QTableWidgetItem("\n".join(warnings) if warnings else "No conflict warnings"),
            )
            self.ranking_table.resizeRowToContents(row)
            if rhu.name == previously_selected_rhu:
                restore_row = row

        if restore_row >= 0:
            self.ranking_table.setCurrentCell(restore_row, 0)

        for rhu_name in licensee.shortlist:
            self.shortlist.addItem(rhu_name)

    def _selected_rhu_name(self) -> str | None:
        """Return the RHU name selected in the ranking table, if any."""
        row = self.ranking_table.currentRow()
        item = self.ranking_table.item(row, 0) if row >= 0 else None
        return str(item.data(Qt.ItemDataRole.UserRole)) if item is not None else None

    def _add_to_shortlist(self) -> None:
        """Store the selected RHU as one of the current licensee's five options."""
        licensee = self._selected_licensee()
        rhu_name = self._selected_rhu_name()
        if licensee is None or rhu_name is None:
            return
        if rhu_name in licensee.shortlist:
            return
        if len(licensee.shortlist) >= 5:
            QMessageBox.information(self, "Shortlist full", "A shortlist can contain up to five RHUs.")
            return
        licensee.shortlist.append(rhu_name)
        self.data_store.update_licensee(licensee)
        self._rank_selected_licensee()

    def _remove_from_shortlist(self) -> None:
        """Remove the selected RHU from the current licensee's shortlist."""
        licensee = self._selected_licensee()
        item = self.shortlist.currentItem()
        if licensee is None or item is None:
            return
        licensee.shortlist.remove(item.text())
        self.data_store.update_licensee(licensee)
        self._rank_selected_licensee()

    def _selected_rhu_warnings(self) -> str:
        """Return the warnings text shown for the currently selected RHU row."""
        row = self.ranking_table.currentRow()
        item = self.ranking_table.item(row, 3) if row >= 0 else None
        return item.text() if item is not None else ""

    def _allocate_selected_rhu(self) -> None:
        """Allocate or transfer the licensee into the selected RHU."""
        licensee = self._selected_licensee()
        rhu_name = self._selected_rhu_name()
        if licensee is None or rhu_name is None:
            return
        rhu = self.data_store.get_rhu(rhu_name)
        if rhu is None:
            return

        warnings = self._selected_rhu_warnings()
        if warnings and warnings != "No conflict warnings":
            response = QMessageBox.question(
                self,
                "Confirm allocation despite warnings",
                f"{rhu.name} has the following warning(s):\n\n{warnings}\n\n"
                "Allocate this licensee here anyway?",
            )
            if response != QMessageBox.StandardButton.Yes:
                return

        is_new_resident = licensee.prison_role_id not in rhu.resident_ids
        maximum_capacity = rhu.capacity + rhu.emergency_capacity
        if is_new_resident and len(rhu.resident_ids) >= maximum_capacity:
            QMessageBox.warning(self, "No bed available", "This RHU has no standard or emergency bed available.")
            return

        try:
            self.data_store.allocate_licensee(licensee.prison_role_id, rhu.name)
        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Could not allocate licensee", str(error))
            return
        QMessageBox.information(self, "Allocation saved", f"{licensee.name} is allocated to {rhu.name}.")
        self.licensee_picker.setCurrentIndex(0)
        self.ranking_table.setRowCount(0)
        self.shortlist.clear()
        self.allocation_changed.emit()