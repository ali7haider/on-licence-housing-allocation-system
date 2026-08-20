"""RHU list management with resident details."""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from models.person import Licensee
from models.rhu import RHU
from ui.rhu_editor import RHUEditor


class RHUListView(QWidget):
    """List RHUs and their current residents, with CRUD controls."""

    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create the RHU search controls and expandable resident tree."""
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search RHUs by name, address, or contact")
        self.search_input.textChanged.connect(self.refresh)
        controls.addWidget(self.search_input)

        add_button = QPushButton("Add new RHU")
        add_button.clicked.connect(self._open_add_editor)
        controls.addWidget(add_button)

        self.edit_button = QPushButton("Edit selected")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._open_edit_editor)
        controls.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete selected")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_selected)
        controls.addWidget(self.delete_button)
        self.incident_button = QPushButton("Record resident incident")
        self.incident_button.setEnabled(False)
        self.incident_button.clicked.connect(self._record_incident)
        controls.addWidget(self.incident_button)
        layout.addLayout(controls)

        self.rhu_tree = QTreeWidget()
        self.rhu_tree.setHeaderLabels(["RHU / Resident", "Residents", "Cost/day", "Capacity / exit", "Contact / incident"])
        self.rhu_tree.setAlternatingRowColors(True)
        self.rhu_tree.itemDoubleClicked.connect(self._open_edit_from_item)
        self.rhu_tree.currentItemChanged.connect(self._update_action_buttons)
        layout.addWidget(self.rhu_tree)

    def refresh(self, *_: object) -> None:
        """Rebuild the RHU tree using the active search text."""
        self.rhu_tree.clear()
        for rhu in self.data_store.search_rhus(self.search_input.text()):
            rhu_item = QTreeWidgetItem(
                [
                    rhu.name,
                    f"{len(rhu.resident_ids)}/{rhu.capacity}",
                    f"£{rhu.cost_per_bed_per_day:.2f}",
                    f"{rhu.capacity} (+{rhu.emergency_capacity})",
                    "",
                    rhu.contact_name or rhu.phone,
                ]
            )
            rhu_item.setData(0, Qt.ItemDataRole.UserRole, rhu.name)
            self.rhu_tree.addTopLevelItem(rhu_item)
            for resident in self._residents_for(rhu):
                exit_text = (
                    resident.housing_exit_date.strftime("%d %b %Y")
                    if resident.housing_exit_date
                    else "not set"
                )
                resident_item = QTreeWidgetItem(
                    [
                        f"{resident.name} ({resident.prison_role_id})",
                        "",
                        "",
                        exit_text,
                        "Incident recorded" if resident.prison_role_id in rhu.incidents else "",
                    ],
                )
                resident_item.setData(0, Qt.ItemDataRole.UserRole, resident.prison_role_id)
                rhu_item.addChild(resident_item)
        self.rhu_tree.resizeColumnToContents(0)
        self._update_action_buttons()

    def _residents_for(self, rhu: RHU) -> list[Licensee]:
        """Return an RHU's resident records ordered by expected housing exit."""
        residents = [
            self.data_store.get_licensee(prison_role_id)
            for prison_role_id in rhu.resident_ids
        ]
        present_residents = [resident for resident in residents if resident is not None]
        return sorted(present_residents, key=lambda resident: resident.housing_exit_date or date.max)

    def _selected_rhu(self) -> RHU | None:
        """Return the selected top-level RHU, ignoring resident child rows."""
        item = self.rhu_tree.currentItem()
        if item is None or item.parent() is not None:
            return None
        return self.data_store.get_rhu(str(item.data(0, Qt.ItemDataRole.UserRole)))

    def _update_action_buttons(self, *_: object) -> None:
        """Enable RHU actions only when a top-level RHU row is selected."""
        has_rhu = self._selected_rhu() is not None
        self.edit_button.setEnabled(has_rhu)
        self.delete_button.setEnabled(has_rhu)
        item = self.rhu_tree.currentItem()
        self.incident_button.setEnabled(item is not None and item.parent() is not None)

    def _open_add_editor(self) -> None:
        """Open an empty RHU editor and refresh after saving."""
        editor = RHUEditor(self.data_store, parent=self)
        if editor.exec():
            self.refresh()

    def _open_edit_from_item(self, item: QTreeWidgetItem, _: int) -> None:
        """Open the selected RHU on double-click, but not a resident child row."""
        if item.parent() is None:
            self._open_edit_editor()

    def _open_edit_editor(self) -> None:
        """Open the selected RHU in its editor and refresh after saving."""
        rhu = self._selected_rhu()
        if rhu is None:
            return
        editor = RHUEditor(self.data_store, rhu, parent=self)
        if editor.exec():
            self.refresh()

    def _delete_selected(self) -> None:
        """Delete an empty RHU after confirmation; residents must be transferred first."""
        rhu = self._selected_rhu()
        if rhu is None:
            return
        if rhu.resident_ids:
            QMessageBox.warning(
                self,
                "RHU has residents",
                "Transfer or exit all current residents before deleting this RHU.",
            )
            return
        response = QMessageBox.question(
            self,
            "Delete RHU",
            f"Delete {rhu.name}? This cannot be undone.",
        )
        if response is QMessageBox.StandardButton.Yes:
            self.data_store.delete_rhu(rhu.name)
            self.refresh()

    def _record_incident(self) -> None:
        """Capture a per-resident violence or disturbance report."""
        item = self.rhu_tree.currentItem()
        if item is None or item.parent() is None:
            return
        rhu = self.data_store.get_rhu(str(item.parent().data(0, Qt.ItemDataRole.UserRole)))
        if rhu is None:
            return
        resident_id = str(item.data(0, Qt.ItemDataRole.UserRole))
        current = rhu.incidents.get(resident_id, "")
        from PySide6.QtWidgets import QInputDialog
        details, accepted = QInputDialog.getMultiLineText(
            self, "Resident incident", "Violence or disturbance report:", current
        )
        if accepted:
            self.data_store.record_incident(rhu.name, resident_id, details)
            self.refresh()
