"""Reusable Qt editor for licensee and RHU matching attributes."""

from collections.abc import Iterable

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.attributes import MatchAttribute, TextAttribute, YesNoAttribute, ZoneAttribute


AttributeDefinition = tuple[str, MatchAttribute]


class TagListWidget(QWidget):
    """A small add/remove tag editor used for exclusion-zone values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Type a zone tag")
        self.tag_input.returnPressed.connect(self.add_tag)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_tag)
        remove_button = QPushButton("Remove selected")
        remove_button.clicked.connect(self.remove_selected)

        input_row = QHBoxLayout()
        input_row.addWidget(self.tag_input)
        input_row.addWidget(add_button)

        self.tag_list = QListWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(input_row)
        layout.addWidget(self.tag_list)
        layout.addWidget(remove_button)

    def add_tag(self) -> None:
        """Add a non-empty, non-duplicate tag from the text input."""
        tag = self.tag_input.text().strip()
        if tag and tag.casefold() not in {item.casefold() for item in self.tags()}:
            self.tag_list.addItem(tag)
        self.tag_input.clear()

    def remove_selected(self) -> None:
        """Remove the selected zone tag, if there is one."""
        row = self.tag_list.currentRow()
        if row >= 0:
            self.tag_list.takeItem(row)

    def tags(self) -> list[str]:
        """Return the currently entered tags in display order."""
        return [self.tag_list.item(index).text() for index in range(self.tag_list.count())]

    def set_tags(self, tags: object) -> None:
        """Replace the displayed tags with a string or iterable of strings."""
        self.tag_list.clear()
        if isinstance(tags, str):
            tag_values = tags.split(",")
        elif isinstance(tags, Iterable):
            tag_values = tags
        else:
            tag_values = []
        for tag in tag_values:
            text = str(tag).strip()
            if text:
                self.tag_list.addItem(text)


class AttributeEditor(QWidget):
    """Render attribute definitions and collect their values in one place."""

    def __init__(
        self,
        definitions: Iterable[AttributeDefinition],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.definitions = list(definitions)
        self.inputs: dict[str, QWidget] = {}

        form = QFormLayout(self)
        for key, attribute in self.definitions:
            input_widget = self._create_input(attribute)
            self.inputs[key] = input_widget
            if isinstance(input_widget, QCheckBox):
                form.addRow(input_widget)
            else:
                form.addRow(QLabel(attribute.label), input_widget)

    def _create_input(self, attribute: MatchAttribute) -> QWidget:
        """Choose the appropriate Qt input from an attribute's concrete type."""
        if isinstance(attribute, YesNoAttribute):
            return QCheckBox(attribute.label)
        if isinstance(attribute, ZoneAttribute):
            return TagListWidget()
        if isinstance(attribute, TextAttribute):
            return QLineEdit()
        raise TypeError(f"Unsupported attribute type: {type(attribute).__name__}")

    def set_values(self, values: dict[str, object]) -> None:
        """Populate the editor from a licensee or RHU attribute dictionary."""
        for key, input_widget in self.inputs.items():
            value = values.get(key)
            if isinstance(input_widget, QCheckBox):
                input_widget.setChecked(bool(value))
            elif isinstance(input_widget, TagListWidget):
                input_widget.set_tags(value)
            elif isinstance(input_widget, QLineEdit):
                input_widget.setText(_display_text(value))

    def values(self) -> dict[str, object]:
        """Return the current values in a form suitable for model attributes."""
        collected: dict[str, object] = {}
        for key, input_widget in self.inputs.items():
            if isinstance(input_widget, QCheckBox):
                collected[key] = input_widget.isChecked()
            elif isinstance(input_widget, TagListWidget):
                collected[key] = input_widget.tags()
            elif isinstance(input_widget, QLineEdit):
                collected[key] = input_widget.text().strip()
        return collected


def _display_text(value: object) -> str:
    """Turn list values into a readable comma-separated text-field value."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        return ", ".join(str(item) for item in value)
    return str(value)
