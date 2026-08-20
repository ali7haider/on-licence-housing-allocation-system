"""Upcoming release list grouped by RHU, with exit-date editing."""

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from logic.releases import change_release_date, upcoming_releases
from models.person import Licensee


class ReleaseDateDialog(QDialog):
    """Small dialog for editing a single licensee's housing exit date."""

    def __init__(self, licensee: Licensee, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Change exit date — {licensee.name}")
        self.licensee = licensee

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{licensee.name} ({licensee.prison_role_id})"))

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(licensee.housing_exit_date or date.today())
        layout.addWidget(self.date_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_date(self) -> date:
        """Return the date chosen in the picker as a plain ``date``."""
        return self.date_input.date().toPython()


class ReleaseListView(QWidget):
    """Show licensees due to leave housing, grouped by RHU, with date editing."""

    #: Emitted after a housing exit date changes, so other tabs can refresh.
    release_changed = Signal()

    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create the release tree and its refresh control."""
        layout = QVBoxLayout(self)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)

        self.release_tree = QTreeWidget()
        self.release_tree.setHeaderLabels(["RHU / Licensee", "Prison Role ID", "Exit Date"])
        self.release_tree.setAlternatingRowColors(True)
        # Double-clicking a licensee (child) row opens the date editor; RHU
        # (top-level) rows are headers only and are ignored.
        self.release_tree.itemDoubleClicked.connect(self._open_date_editor)
        layout.addWidget(self.release_tree)

    def refresh(self, *_: object) -> None:
        """Rebuild the tree from the current release-date data."""
        self.release_tree.clear()
        grouped = upcoming_releases(self.data_store.list_licensees())
        for rhu_name, residents in grouped.items():
            rhu_item = QTreeWidgetItem([rhu_name, "", ""])
            self.release_tree.addTopLevelItem(rhu_item)
            for resident in residents:
                resident_item = QTreeWidgetItem(
                    [
                        resident.name,
                        resident.prison_role_id,
                        resident.housing_exit_date.strftime("%d %b %Y"),
                    ]
                )
                resident_item.setData(0, Qt.ItemDataRole.UserRole, resident.prison_role_id)
                rhu_item.addChild(resident_item)
            rhu_item.setExpanded(False)
        self.release_tree.resizeColumnToContents(0)

    def _open_date_editor(self, item: QTreeWidgetItem, _: int) -> None:
        """Open the date dialog for a double-clicked resident row."""
        if item.parent() is None:
            return  # An RHU header row was double-clicked; nothing to edit.

        prison_role_id = str(item.data(0, Qt.ItemDataRole.UserRole))
        licensee = self.data_store.get_licensee(prison_role_id)
        if licensee is None:
            return

        dialog = ReleaseDateDialog(licensee, parent=self)
        if not dialog.exec():
            return

        new_date = dialog.selected_date()
        warning_required = change_release_date(licensee, new_date)
        self.data_store.update_licensee(licensee)

        if warning_required:
            QMessageBox.warning(
                self,
                "Exit date moved back",
                f"{licensee.name}'s housing exit date has been moved later, "
                f"to {new_date:%d %b %Y}. Please confirm this is intended.",
            )

        self.refresh()
        self.release_changed.emit()