"""Main application window shell."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget


class MainWindow(QMainWindow):
    """The window shown after the allocation officer enters the password."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("On-Licence Housing Allocation System")
        self.setMinimumSize(900, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        for tab_name in ("Licensees", "RHUs", "Allocation", "Releases", "Costs"):
            self.tabs.addTab(QWidget(), tab_name)
