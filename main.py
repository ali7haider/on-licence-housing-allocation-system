"""Application entry point for the On-Licence Housing Allocation System."""

import sys

from PySide6.QtWidgets import QApplication

from ui.login_window import LoginWindow


def main() -> int:
    """Start the password-only login window and the Qt event loop."""
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
