"""Entry point for the Induction Heating Simulator application."""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Induction Heating Simulator")
        self.setMinimumSize(800, 600)
        label = QLabel("Induction Heating Simulator\n\nReady.", alignment=Qt.AlignCenter)
        self.setCentralWidget(label)


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
