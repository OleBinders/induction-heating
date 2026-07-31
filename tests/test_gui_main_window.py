"""Tests for the main application window."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMainWindow, QToolBar

from induction_heating.gui.main_window import MainWindow


@pytest.fixture
def window(qtbot) -> MainWindow:
    """Create a MainWindow for testing."""
    w = MainWindow()
    qtbot.addWidget(w)
    return w


class TestMainWindow:
    """Test main window creation and structure."""

    def test_creates_without_errors(self, window: MainWindow) -> None:
        """MainWindow creates without errors."""
        assert window is not None

    def test_window_title(self, window: MainWindow) -> None:
        """Window title is correct."""
        assert window.windowTitle() == "Induction Heating Simulator"

    def test_minimum_size(self, window: MainWindow) -> None:
        """Minimum size is 1024x768."""
        assert window.minimumSize().width() == 1024
        assert window.minimumSize().height() == 768

    def test_is_qmainwindow(self, window: MainWindow) -> None:
        """MainWindow is a QMainWindow."""
        assert isinstance(window, QMainWindow)

    def test_menu_bar_exists(self, window: MainWindow) -> None:
        """Menu bar exists."""
        assert window.menuBar() is not None

    def test_toolbar_exists(self, window: MainWindow) -> None:
        """Toolbar exists."""
        toolbars = window.findChildren(QToolBar)
        assert len(toolbars) > 0

    def test_status_bar_exists(self, window: MainWindow) -> None:
        """Status bar exists."""
        assert window.statusBar() is not None

    def test_status_bar_ready(self, window: MainWindow) -> None:
        """Status bar shows Ready."""
        assert "Ready" in window.statusBar().currentMessage()

    def test_params_dock_exists(self, window: MainWindow) -> None:
        """Parameters dock widget exists."""
        assert window.params_dock is not None
        assert window.params_dock.windowTitle() == "Parameters"

    def test_results_dock_exists(self, window: MainWindow) -> None:
        """Results dock widget exists."""
        assert window.results_dock is not None
        assert window.results_dock.windowTitle() == "Results"

    def test_run_action_exists(self, window: MainWindow) -> None:
        """Run action exists on toolbar."""
        assert window.run_action is not None

    def test_save_action_exists(self, window: MainWindow) -> None:
        """Save action exists on toolbar."""
        assert window.save_action is not None

    def test_load_action_exists(self, window: MainWindow) -> None:
        """Load action exists on toolbar."""
        assert window.load_action is not None

    def test_export_action_exists(self, window: MainWindow) -> None:
        """Export action exists on toolbar."""
        assert window.export_action is not None
