"""Entry point for the Induction Heating Simulator application."""

import sys

from PySide6.QtWidgets import QApplication

from induction_heating.gui.main_window import MainWindow


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Induction Heating Simulator")
    app.setOrganizationName("InductionHeating")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
