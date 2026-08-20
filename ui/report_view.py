"""Operational report generation and export view."""

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logic.data_store import DataStore
from logic.reports import build_operational_report


class ReportView(QWidget):
    """Display a current operational report and allow it to be saved as text."""

    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create report generation, export, and preview controls."""
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()

        refresh_button = QPushButton("Generate report")
        refresh_button.clicked.connect(self.refresh)
        controls.addWidget(refresh_button)

        save_button = QPushButton("Save report")
        save_button.clicked.connect(self._save_report)
        controls.addWidget(save_button)
        layout.addLayout(controls)

        self.report_text = QPlainTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)

    def refresh(self, *_: object) -> None:
        """Generate the report from the current in-memory records."""
        self.report_text.setPlainText(
            build_operational_report(
                self.data_store.list_licensees(),
                self.data_store.list_rhus(),
            )
        )

    def _save_report(self) -> None:
        """Save the visible report to a user-selected text file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save operational report",
            "housing_allocation_report.txt",
            "Text files (*.txt)",
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as report_file:
                report_file.write(self.report_text.toPlainText())
