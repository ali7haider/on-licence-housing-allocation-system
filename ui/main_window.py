"""Main application window shell."""

from PySide6.QtWidgets import QMainWindow, QTabWidget

from logic.data_store import DataStore
from logic.sample_data import generate_sample_data
from ui.allocation_view import AllocationView
from ui.cost_view import CostView
from ui.licensee_list_view import LicenseeListView
from ui.release_view import ReleaseListView
from ui.rhu_list_view import RHUListView


class MainWindow(QMainWindow):
    """The window shown after the allocation officer enters the password."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("On-Licence Housing Allocation System")
        self.setMinimumSize(900, 600)
        licensees, rhus = generate_sample_data()
        self.data_store = DataStore(licensees, rhus)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.licensee_list_view = LicenseeListView(self.data_store)
        self.rhu_list_view = RHUListView(self.data_store)
        self.allocation_view = AllocationView(self.data_store)
        self.release_view = ReleaseListView(self.data_store)
        self.cost_view = CostView(self.data_store)
        self.allocation_view.allocation_changed.connect(self.licensee_list_view.refresh)
        self.allocation_view.allocation_changed.connect(self.rhu_list_view.refresh)
        self.allocation_view.allocation_changed.connect(self.release_view.refresh)
        self.allocation_view.allocation_changed.connect(self.cost_view.refresh)
        self.licensee_list_view.record_changed.connect(self.rhu_list_view.refresh)
        self.licensee_list_view.record_changed.connect(self.allocation_view.refresh)
        self.licensee_list_view.record_changed.connect(self.release_view.refresh)
        self.licensee_list_view.record_changed.connect(self.cost_view.refresh)
        self.tabs.addTab(self.licensee_list_view, "Licensees")
        self.tabs.addTab(self.rhu_list_view, "RHUs")
        self.tabs.addTab(self.allocation_view, "Allocation")
        self.tabs.addTab(self.release_view, "Releases")
        self.tabs.addTab(self.cost_view, "Costs")
