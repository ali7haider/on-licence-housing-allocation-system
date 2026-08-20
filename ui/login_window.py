"""Password-only entry screen for the Durham allocation officer."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.main_window import MainWindow


PASSWORD = "durham2026"


class LoginWindow(QWidget):
    """Open the main window after a correct password is entered."""

    def __init__(self) -> None:
        super().__init__()
        self.main_window: MainWindow | None = None
        self.setWindowTitle("Housing Allocation Login")
        self.setFixedWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        """Create the intentionally simple password-only form."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter the allocation officer password:"))

        password_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.returnPressed.connect(self._login)
        password_row.addWidget(self.password_input)

        login_button = QPushButton("Log in")
        login_button.clicked.connect(self._login)
        password_row.addWidget(login_button)
        layout.addLayout(password_row)

    def _login(self) -> None:
        """Open the main window when the hardcoded password is correct."""
        if self.password_input.text() == PASSWORD:
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
            return

        QMessageBox.warning(self, "Incorrect password", "Please enter the correct password.")
        self.password_input.clear()
        self.password_input.setFocus()
