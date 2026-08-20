
"""Running housing cost totals with a manual "add a day" and payment reset."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from logic.costs import add_day, is_overspending, mark_paid, projected_cost
from logic.data_store import DataStore
from models.rhu import RHU


class CostView(QWidget):
    """Show each RHU's running cost, with per-day accrual and a paid reset."""

    def __init__(self, data_store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data_store = data_store
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create the budget control, action buttons, and the cost tree."""
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Budget per RHU (£):"))
        self.budget_input = QDoubleSpinBox()
        self.budget_input.setRange(0, 100_000)
        self.budget_input.setDecimals(2)
        self.budget_input.setValue(500.00)
        # Changing the budget only changes the over/under flag, not the totals.
        self.budget_input.valueChanged.connect(self.refresh)
        controls.addWidget(self.budget_input)

        add_day_button = QPushButton("Add a day's cost")
        add_day_button.setToolTip("Accrue one day's placement cost for every occupied RHU.")
        add_day_button.clicked.connect(self._add_day_all)
        controls.addWidget(add_day_button)

        self.pay_button = QPushButton("Mark selected as paid")
        self.pay_button.setEnabled(False)
        self.pay_button.clicked.connect(self._pay_selected)
        controls.addWidget(self.pay_button)
        layout.addLayout(controls)

        self.cost_tree = QTreeWidget()
        self.cost_tree.setHeaderLabels(
            [
                "RHU",
                "Residents",
                "Cost/bed/day",
                "Total owed",
                "Projected 30 days",
                "Last paid",
                "Status",
            ]
        )
        self.cost_tree.setAlternatingRowColors(True)
        self.cost_tree.currentItemChanged.connect(self._update_pay_button)
        layout.addWidget(self.cost_tree)

    def refresh(self, *_: object) -> None:
        """Rebuild the cost tree from the current RHU totals and budget."""
        self.cost_tree.clear()
        budget = self.budget_input.value()
        for rhu in self.data_store.list_rhus():
            overspending = is_overspending(rhu, budget)
            forecast = projected_cost(rhu)
            forecast_overspending = forecast > budget
            if overspending:
                status = "Over budget now"
            elif forecast_overspending:
                status = "Projected over budget"
            else:
                status = "Within budget"
            item = QTreeWidgetItem(
                [
                    rhu.name,
                    str(len(rhu.resident_ids)),
                    f"£{rhu.cost_per_bed_per_day:.2f}",
                    f"£{rhu.total_owed:.2f}",
                    f"£{forecast:.2f}",
                    rhu.last_payment_date.strftime("%d %b %Y"),
                    status,
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, rhu.name)
            item.setForeground(
                6,
                QColor("red") if overspending or forecast_overspending else QColor("green"),
            )
            self.cost_tree.addTopLevelItem(item)
        self.cost_tree.resizeColumnToContents(0)
        self._update_pay_button()

    def _selected_rhu(self) -> RHU | None:
        """Return the RHU behind the currently selected row, if any."""
        item = self.cost_tree.currentItem()
        if item is None:
            return None
        return self.data_store.get_rhu(str(item.data(0, Qt.ItemDataRole.UserRole)))

    def _update_pay_button(self, *_: object) -> None:
        """Enable the pay button only while an RHU row is selected."""
        self.pay_button.setEnabled(self._selected_rhu() is not None)

    def _add_day_all(self) -> None:
        """Accrue one day's cost for every RHU that currently has residents."""
        for rhu in self.data_store.list_rhus():
            if rhu.resident_ids:
                add_day(rhu)
        self.refresh()

    def _pay_selected(self) -> None:
        """Reset the selected RHU's running total to zero after confirmation."""
        rhu = self._selected_rhu()
        if rhu is None:
            return
        if rhu.total_owed <= 0:
            QMessageBox.information(self, "Nothing owed", f"{rhu.name} has no outstanding cost.")
            return
        response = QMessageBox.question(
            self,
            "Confirm payment",
            f"Mark £{rhu.total_owed:.2f} as paid for {rhu.name}?",
        )
        if response is QMessageBox.StandardButton.Yes:
            mark_paid(rhu)
            self.refresh()