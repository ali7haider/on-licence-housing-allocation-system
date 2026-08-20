"""Three-column licensee board with search, sorting, and state movement."""

from collections.abc import Callable, Iterable
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from models.enums import LicenseeState
from models.person import Licensee
from ui.licensee_editor import LicenseeEditor
from PySide6.QtCore import Qt, Signal


class StateListWidget(QListWidget):
    """A list that reports a drag-and-drop move to its target licence state."""

    def __init__(
        self,
        state: LicenseeState,
        moved_callback: Callable[[list[str], LicenseeState], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.moved_callback = moved_callback
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event: QDropEvent) -> None:
        """Move the Qt item, then update the underlying licensee state."""
        source = event.source()
        role = Qt.ItemDataRole.UserRole
        moved_ids = (
            [str(item.data(role)) for item in source.selectedItems()]
            if isinstance(source, QListWidget)
            else []
        )
        super().dropEvent(event)
        if moved_ids:
            self.moved_callback(moved_ids, self.state)


class LicenseeListView(QWidget):
    """Display pending, allocated, and exited licensees in sortable columns."""
    record_changed = Signal() 
    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self.state_lists: dict[LicenseeState, StateListWidget] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create board controls and the three licence-state lists."""
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, prison role ID, address, or location")
        self.search_input.textChanged.connect(self.refresh)
        controls.addWidget(self.search_input)

        self.sort_input = QComboBox()
        self.sort_input.addItems(["Relevant date", "Name"])
        self.sort_input.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.sort_input)

        add_button = QPushButton("Add new licensee")
        add_button.clicked.connect(self._open_add_editor)
        controls.addWidget(add_button)
        layout.addLayout(controls)

        columns = QHBoxLayout()
        for state in LicenseeState:
            column = QVBoxLayout()
            column.addWidget(QLabel(state.value))
            state_list = StateListWidget(state, self._move_licensees)
            state_list.itemDoubleClicked.connect(self._open_edit_editor)
            self.state_lists[state] = state_list
            column.addWidget(state_list)
            columns.addLayout(column)
        layout.addLayout(columns)

    def refresh(self, *_: object) -> None:
        """Repopulate all columns using the current search and sort controls."""
        matching_ids = {
            licensee.prison_role_id
            for licensee in self.data_store.search_licensees(self.search_input.text())
        }
        for state, state_list in self.state_lists.items():
            state_list.clear()
            licensees = [
                licensee
                for licensee in self.data_store.list_licensees(state)
                if licensee.prison_role_id in matching_ids
            ]
            for licensee in self._sort_licensees(licensees, state):
                item = QListWidgetItem(self._display_text(licensee, state))
                item.setData(Qt.ItemDataRole.UserRole, licensee.prison_role_id)
                state_list.addItem(item)

    def _sort_licensees(
        self,
        licensees: Iterable[Licensee],
        state: LicenseeState,
    ) -> list[Licensee]:
        """Sort by name or the date relevant to the selected state."""
        if self.sort_input.currentText() == "Name" or state is LicenseeState.EXITED:
            return sorted(licensees, key=lambda licensee: licensee.name.casefold())
        if state is LicenseeState.PENDING:
            return sorted(licensees, key=lambda licensee: licensee.release_date)
        return sorted(licensees, key=lambda licensee: licensee.housing_exit_date or date.max)

    @staticmethod
    def _display_text(licensee: Licensee, state: LicenseeState) -> str:
        """Build a concise state-appropriate board item label."""
        if state is LicenseeState.PENDING:
            detail = f"Release: {licensee.release_date:%d %b %Y}"
        elif state is LicenseeState.ALLOCATED:
            exit_date = licensee.housing_exit_date
            detail = f"Exit: {exit_date:%d %b %Y}" if exit_date else "Exit: not set"
        else:
            detail = "Exited"
        return f"{licensee.name} ({licensee.prison_role_id})\n{detail}"

    def _move_licensees(self, prison_role_ids: list[str], state: LicenseeState) -> None:
        """Apply a dropped column's state to its licensees and redraw the board."""
        blocked: list[str] = []
        for prison_role_id in prison_role_ids:
            try:
                self.data_store.transition_licensee_state(prison_role_id, state)
            except (KeyError, ValueError) as error:
                blocked.append(str(error))
        if blocked:
            QMessageBox.warning(self, "Could not move licensee", "\n".join(blocked))
        self.refresh()
        self.record_changed.emit()

    def _open_add_editor(self) -> None:
        """Open an empty editor and redraw after a successful save."""
        editor = LicenseeEditor(self.data_store, parent=self)
        if editor.exec():
            self.refresh()
            self.record_changed.emit()

    def _open_edit_editor(self, item: QListWidgetItem) -> None:
        """Open the selected licensee for editing when its item is double-clicked."""
        licensee = self.data_store.get_licensee(str(item.data(Qt.ItemDataRole.UserRole)))
        if licensee is None:
            return
        editor = LicenseeEditor(self.data_store, licensee, parent=self)
        if editor.exec():
            self.refresh()
            self.record_changed.emit()
