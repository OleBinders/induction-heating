"""Main application window for the Induction Heating Simulator."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QScrollArea,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from induction_heating.core.geometry import CylindricalWorkpiece, InductionSetup, SolenoidCoil
from induction_heating.gui.panels.material_panel import MaterialPanel
from induction_heating.gui.panels.param_panel import CoilPanel, OperatingPanel, WorkpiecePanel
from induction_heating.gui.views.cross_section_view import CrossSectionView
from induction_heating.materials.database import MaterialDatabase


class MainWindow(QMainWindow):
    """Main application window with docked panels, menu bar, toolbar, and status bar."""

    def __init__(self, material_db: MaterialDatabase | None = None) -> None:
        super().__init__()
        self._db = material_db or MaterialDatabase()
        self._setup_ui()
        self._connect_signals()
        self._validate_inputs()

    def _setup_ui(self) -> None:
        """Set up the main window layout."""
        self.setWindowTitle("Induction Heating Simulator")
        self.setMinimumSize(1024, 768)

        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_dock_widgets()
        self._setup_status_bar()

    def _setup_menu_bar(self) -> None:
        """Create menu bar with File, Edit, View, Help menus."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("New")
        file_menu.addAction("Open...")
        file_menu.addAction("Save")
        file_menu.addAction("Save As...")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction("Copy")
        edit_menu.addAction("Paste")
        edit_menu.addSeparator()
        edit_menu.addAction("Preferences...")

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction("Reset Layout")

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About")

    def _setup_tool_bar(self) -> None:
        """Create toolbar with Run, Save, Load, Export actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.run_action = QAction("▶ Run", self)
        self.run_action.setToolTip("Run calculation")
        self.run_action.setEnabled(False)
        toolbar.addAction(self.run_action)

        toolbar.addSeparator()

        self.save_action = QAction("💾 Save", self)
        self.save_action.setToolTip("Save simulation")
        toolbar.addAction(self.save_action)

        self.load_action = QAction("📂 Load", self)
        self.load_action.setToolTip("Load simulation")
        toolbar.addAction(self.load_action)

        self.export_action = QAction("📤 Export", self)
        self.export_action.setToolTip("Export results")
        toolbar.addAction(self.export_action)

    def _setup_dock_widgets(self) -> None:
        """Create left (Parameters) and right (Results) dock widgets."""
        # Left dock: Parameters
        self.params_dock = QDockWidget("Parameters", self)
        self.params_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Scrollable container for parameter panels
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        params_container = QWidget()
        params_layout = QVBoxLayout(params_container)

        self.coil_panel = CoilPanel()
        self.workpiece_panel = WorkpiecePanel()
        self.operating_panel = OperatingPanel()
        self.material_panel = MaterialPanel(self._db)

        params_layout.addWidget(self.coil_panel)
        params_layout.addWidget(self.workpiece_panel)
        params_layout.addWidget(self.operating_panel)
        params_layout.addWidget(self.material_panel)
        params_layout.addStretch()

        scroll.setWidget(params_container)
        self.params_dock.setWidget(scroll)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.params_dock)

        # Right dock: Results
        self.results_dock = QDockWidget("Results", self)
        self.results_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)

        # Cross-section view with view toggle
        view_toggle_layout = QHBoxLayout()
        view_toggle_layout.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItem("Magnetic Field (B)")
        self.view_combo.addItem("Power Density (P)")
        view_toggle_layout.addWidget(self.view_combo)
        view_toggle_layout.addStretch()

        self.cross_section_view = CrossSectionView()
        results_layout.addLayout(view_toggle_layout)
        results_layout.addWidget(self.cross_section_view, stretch=3)

        # Placeholder for numerical results and plots
        results_layout.addWidget(QGroupBox("Numerical Results"), stretch=1)
        results_layout.addWidget(QGroupBox("Plots"), stretch=1)

        self.results_dock.setWidget(results_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.results_dock)

    def _setup_status_bar(self) -> None:
        """Create status bar showing Ready."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self) -> None:
        """Connect panel signals to validation and Run button."""
        self.coil_panel.changed.connect(self._validate_inputs)
        self.workpiece_panel.changed.connect(self._validate_inputs)
        self.operating_panel.changed.connect(self._validate_inputs)
        self.material_panel.material_changed.connect(self._validate_inputs)

        # Run button
        self.run_action.triggered.connect(self._run_calculation)

        # View toggle
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)

    def _validate_inputs(self) -> bool:
        """Validate all inputs and update status bar and Run button.

        Returns:
            True if all inputs are valid.
        """
        errors = []

        # Cross-field validation: workpiece radius < coil inner radius
        wp_radius = self.workpiece_panel.radius_spin.value()
        coil_inner = self.coil_panel.inner_radius_spin.value()

        if wp_radius >= coil_inner:
            errors.append(
                f"Workpiece radius ({wp_radius:.4f} m) must be less than "
                f"coil inner radius ({coil_inner:.4f} m)"
            )

        # Outer radius >= inner radius
        coil_outer = self.coil_panel.outer_radius_spin.value()
        if coil_outer < coil_inner:
            errors.append("Coil outer radius must be >= inner radius")

        if errors:
            self.status_bar.showMessage(" | ".join(errors))
            palette = self.status_bar.palette()
            palette.setColor(QPalette.ColorRole.WindowText, QColor("red"))
            self.status_bar.setPalette(palette)
            self.run_action.setEnabled(False)
            return False

        # All valid
        self.status_bar.showMessage("Ready")
        palette = self.status_bar.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("green"))
        self.status_bar.setPalette(palette)
        self.run_action.setEnabled(True)
        return True

    def get_setup(self) -> InductionSetup:
        """Create InductionSetup from current panel values.

        Returns:
            InductionSetup with current parameters.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not self._validate_inputs():
            raise ValueError("Invalid inputs")

        coil = SolenoidCoil(
            inner_radius=self.coil_panel.inner_radius_spin.value(),
            outer_radius=self.coil_panel.outer_radius_spin.value(),
            length=self.coil_panel.length_spin.value(),
            turns=self.coil_panel.turns_spin.value(),
            wire_diameter=self.coil_panel.wire_diameter_spin.value(),
        )
        workpiece = CylindricalWorkpiece(
            radius=self.workpiece_panel.radius_spin.value(),
            length=self.workpiece_panel.length_spin.value(),
            material_name=self.material_panel.selected_material,
        )
        gap = coil.inner_radius - workpiece.radius
        return InductionSetup(coil=coil, workpiece=workpiece, gap=gap)

    def _run_calculation(self) -> None:
        """Run the induction heating calculation and update the cross-section view."""
        try:
            setup = self.get_setup()
        except ValueError:
            return

        current = self.operating_panel.current_spin.value()
        frequency = self.operating_panel.frequency_spin.value()

        self.status_bar.showMessage("Calculating...")
        self.cross_section_view.calculate_and_plot_field(setup, current)
        self.status_bar.showMessage("Calculation complete")

    def _on_view_changed(self, index: int) -> None:
        """Handle view toggle change."""
        if index == 0:
            self.cross_section_view.set_view("b_field")
        else:
            self.cross_section_view.set_view("power_density")
