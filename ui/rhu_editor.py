"""Create and edit Rehabilitation Housing Unit records."""

from datetime import date

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from logic.matching import MATCHING_RULES
from models.rhu import RHU
from ui.attribute_editor import AttributeDefinition, AttributeEditor


RHU_ATTRIBUTE_DEFINITIONS: tuple[AttributeDefinition, ...] = tuple(
    (rhu_key, attribute) for _, rhu_key, attribute in MATCHING_RULES
)


class RHUEditor(QDialog):
    """A dialog that saves a new or edited RHU to an in-memory store."""

    def __init__(
        self,
        data_store: DataStore,
        rhu: RHU | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self.rhu = rhu
        self.setWindowTitle("Add RHU" if rhu is None else "Edit RHU")
        self.setMinimumWidth(560)
        self.resize(680, 720)
        self._build_ui()
        if rhu is not None:
            self._load_rhu(rhu)

    def _build_ui(self) -> None:
        """Create the RHU-only form fields and shared matching-attribute form."""
        layout = QVBoxLayout(self)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.management_group_input = QLineEdit()
        self.contact_name_input = QLineEdit()
        self.cost_input = _money_input()
        self.capacity_input = _whole_number_input()
        self.emergency_capacity_input = _whole_number_input()
        self.short_term_beds_input = _whole_number_input()
        self.location_x_input = _coordinate_input()
        self.location_y_input = _coordinate_input()
        self.notes_input = QPlainTextEdit()
        self.notes_input.setFixedHeight(70)

        form.addRow("RHU name", self.name_input)
        form.addRow("Address", self.address_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Management group", self.management_group_input)
        form.addRow("Contact name", self.contact_name_input)
        form.addRow("Cost per bed per day (£)", self.cost_input)
        form.addRow("Standard capacity", self.capacity_input)
        form.addRow("Emergency capacity", self.emergency_capacity_input)
        form.addRow("Short-term beds", self.short_term_beds_input)
        form.addRow("Location X", self.location_x_input)
        form.addRow("Location Y", self.location_y_input)
        form.addRow("Notes", self.notes_input)
        form_layout.addLayout(form)

        self.attribute_editor = AttributeEditor(RHU_ATTRIBUTE_DEFINITIONS)
        form_layout.addWidget(self.attribute_editor)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(form_container)
        layout.addWidget(scroll_area, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_rhu(self, rhu: RHU) -> None:
        """Populate the editor without changing an existing RHU's name identity."""
        self.name_input.setText(rhu.name)
        self.name_input.setReadOnly(True)
        self.address_input.setText(rhu.address)
        self.phone_input.setText(rhu.phone)
        self.email_input.setText(rhu.email)
        self.management_group_input.setText(rhu.management_group)
        self.contact_name_input.setText(rhu.contact_name)
        self.cost_input.setValue(rhu.cost_per_bed_per_day)
        self.capacity_input.setValue(rhu.capacity)
        self.emergency_capacity_input.setValue(rhu.emergency_capacity)
        self.short_term_beds_input.setValue(rhu.short_term_beds)
        self.location_x_input.setValue(rhu.geographic_location[0])
        self.location_y_input.setValue(rhu.geographic_location[1])
        self.notes_input.setPlainText(rhu.notes)
        self.attribute_editor.set_values(rhu.attributes)

    def _save(self) -> None:
        """Validate the RHU name and save its entered details to the store."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing information", "An RHU name is required.")
            return

        existing = self.rhu
        record = RHU(
            name=name,
            address=self.address_input.text().strip(),
            phone=self.phone_input.text().strip(),
            email=self.email_input.text().strip(),
            management_group=self.management_group_input.text().strip(),
            contact_name=self.contact_name_input.text().strip(),
            cost_per_bed_per_day=self.cost_input.value(),
            capacity=self.capacity_input.value(),
            emergency_capacity=self.emergency_capacity_input.value(),
            short_term_beds=self.short_term_beds_input.value(),
            geographic_location=(self.location_x_input.value(), self.location_y_input.value()),
            notes=self.notes_input.toPlainText().strip(),
            attributes=self.attribute_editor.values(),
            resident_ids=list(existing.resident_ids) if existing else [],
            incidents=dict(existing.incidents) if existing else {},
            total_owed=existing.total_owed if existing else 0.0,
            last_payment_date=existing.last_payment_date if existing else date.today(),
        )
        try:
            if existing is None:
                self.data_store.add_rhu(record)
            else:
                self.data_store.update_rhu(record)
        except (KeyError, ValueError) as error:
            QMessageBox.warning(self, "Could not save RHU", str(error))
            return
        self.accept()


def _money_input() -> QDoubleSpinBox:
    """Create a two-decimal money input for a daily bed cost."""
    input_widget = QDoubleSpinBox()
    input_widget.setRange(0, 10_000)
    input_widget.setDecimals(2)
    input_widget.setSingleStep(1.0)
    return input_widget


def _whole_number_input() -> QSpinBox:
    """Create a non-negative whole-number capacity input."""
    input_widget = QSpinBox()
    input_widget.setRange(0, 10_000)
    return input_widget


def _coordinate_input() -> QDoubleSpinBox:
    """Create a flexible coordinate input for the pilot's X/Y location fields."""
    input_widget = QDoubleSpinBox()
    input_widget.setRange(-180, 180)
    input_widget.setDecimals(5)
    return input_widget
