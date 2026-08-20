"""Main application window shell."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from logic.data_store import DataStore
from logic.sample_data import generate_sample_data
from ui.licensee_list_view import LicenseeListView
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
        self.tabs.addTab(self.licensee_list_view, "Licensees")
        self.tabs.addTab(self.rhu_list_view, "RHUs")
        for tab_name in ("Allocation", "Releases", "Costs"):
            self.tabs.addTab(QWidget(), tab_name)
