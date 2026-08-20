"""Create and edit licensee records."""

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from logic.matching import MATCHING_RULES
from models.enums import Category, Gender, LicenseeState
from models.person import Licensee
from ui.attribute_editor import AttributeDefinition, AttributeEditor


LICENSEE_ATTRIBUTE_DEFINITIONS: tuple[AttributeDefinition, ...] = tuple(
    (licensee_key, attribute)
    for licensee_key, _, attribute in MATCHING_RULES
    if licensee_key not in {"category", "gender"}
)


class LicenseeEditor(QDialog):
    """A dialog that saves a new or edited licensee to an in-memory store."""

    def __init__(
        self,
        data_store: DataStore,
        licensee: Licensee | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self.licensee = licensee
        self.setWindowTitle("Add Licensee" if licensee is None else "Edit Licensee")
        self.setMinimumWidth(560)
        self._build_ui()
        if licensee is not None:
            self._load_licensee(licensee)

    def _build_ui(self) -> None:
        """Create the identifying fields, shared attribute editor, and actions."""
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.role_id_input = QLineEdit()
        self.address_input = QLineEdit()
        self.gender_input = _enum_combo(Gender)
        self.category_input = _enum_combo(Category)
        self.state_input = _enum_combo(LicenseeState)
        self.current_location_input = QLineEdit()
        self.release_date_input = _date_input(date.today())
        self.licence_end_date_input = _date_input(date.today())
        self.notes_input = QPlainTextEdit()
        self.notes_input.setFixedHeight(70)

        form.addRow("Name", self.name_input)
        form.addRow("Prison role ID", self.role_id_input)
        form.addRow("Home address", self.address_input)
        form.addRow("Gender", self.gender_input)
        form.addRow("Category", self.category_input)
        form.addRow("Current location", self.current_location_input)
        form.addRow("Prison release date", self.release_date_input)
        form.addRow("Expected end of licence", self.licence_end_date_input)
        form.addRow("State", self.state_input)
        form.addRow("Notes", self.notes_input)
        layout.addLayout(form)

        self.attribute_editor = AttributeEditor(LICENSEE_ATTRIBUTE_DEFINITIONS)
        layout.addWidget(self.attribute_editor)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_licensee(self, licensee: Licensee) -> None:
        """Populate the form while preserving the existing record identity."""
        self.name_input.setText(licensee.name)
        self.role_id_input.setText(licensee.prison_role_id)
        self.role_id_input.setReadOnly(True)
        self.address_input.setText(licensee.home_address)
        _set_combo_value(self.gender_input, licensee.gender)
        _set_combo_value(self.category_input, licensee.category)
        _set_combo_value(self.state_input, licensee.state)
        self.current_location_input.setText(licensee.current_location)
        self.release_date_input.setDate(QDate(licensee.release_date))
        self.licence_end_date_input.setDate(QDate(licensee.licence_end_date))
        self.notes_input.setPlainText(licensee.notes)
        self.attribute_editor.set_values(licensee.attributes)

    def _save(self) -> None:
        """Validate the form and store the resulting licensee record."""
        name = self.name_input.text().strip()
        role_id = self.role_id_input.text().strip()
        if not name or not role_id:
            QMessageBox.warning(self, "Missing information", "Name and prison role ID are required.")
            return

        existing = self.licensee
        record = Licensee(
            name=name,
            prison_role_id=role_id,
            home_address=self.address_input.text().strip(),
            gender=self.gender_input.currentData(),
            release_date=self.release_date_input.date().toPython(),
            licence_end_date=self.licence_end_date_input.date().toPython(),
            current_location=self.current_location_input.text().strip(),
            category=self.category_input.currentData(),
            state=self.state_input.currentData(),
            notes=self.notes_input.toPlainText().strip(),
            attributes=self.attribute_editor.values(),
            current_rhu_name=existing.current_rhu_name if existing else None,
            housing_exit_date=existing.housing_exit_date if existing else None,
            shortlist=list(existing.shortlist) if existing else [],
        )
        try:
            if existing is None:
                self.data_store.add_licensee(record)
            else:
                self.data_store.update_licensee(record)
        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Could not save licensee", str(error))
            return
        self.accept()


def _enum_combo(enum_type: type[Gender] | type[Category] | type[LicenseeState]) -> QComboBox:
    """Create a combo box that stores enum members as its item data."""
    combo = QComboBox()
    for member in enum_type:
        combo.addItem(member.value, member)
    return combo


def _set_combo_value(combo: QComboBox, value: object) -> None:
    """Select the combo-box item whose stored value equals ``value``."""
    combo.setCurrentIndex(combo.findData(value))


def _date_input(initial_date: date) -> QDateEdit:
    """Create a calendar-enabled date field with a supplied default."""
    date_input = QDateEdit(QDate(initial_date))
    date_input.setCalendarPopup(True)
    date_input.setDisplayFormat("dd MMM yyyy")
    return date_input
