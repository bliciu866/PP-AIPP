from __future__ import annotations

from pathlib import Path

from .qt import QtCore, QtGui, QtWidgets
from .settings_dialog import SettingsDialog
from .state import BuildStage, DesktopState
from .theme import APP_STYLESHEET
from .widgets import BuildConsole, ProjectTree


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, kernel=None):
        super().__init__()
        self.kernel = kernel
        self.state = DesktopState()
        self.setWindowTitle("PP-AIPP Beta — AI Publishing Platform")
        self.resize(1100, 720)
        self.setMinimumSize(820, 560)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_central()
        self._build_status()
        self.console.write("PP-AIPP Desktop initialized.")
        self.console.write("Ready.")

    def _build_actions(self) -> None:
        self.open_project_action = QtGui.QAction("Open Project", self)
        self.open_project_action.setShortcut("Ctrl+O")
        self.open_project_action.triggered.connect(self.open_project)

        self.import_action = QtGui.QAction("Import Gold Master", self)
        self.import_action.triggered.connect(self.import_gold_master)

        self.validate_action = QtGui.QAction("Validate", self)
        self.validate_action.triggered.connect(self.validate_project)

        self.build_action = QtGui.QAction("Build Book", self)
        self.build_action.triggered.connect(self.build_book)

        self.export_action = QtGui.QAction("Export", self)
        self.export_action.triggered.connect(self.export_book)

        self.settings_action = QtGui.QAction("Settings", self)
        self.settings_action.triggered.connect(self.open_settings)

        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.import_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        build_menu = self.menuBar().addMenu("&Build")
        build_menu.addAction(self.validate_action)
        build_menu.addAction(self.build_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self.settings_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        for action in (
            self.open_project_action,
            self.import_action,
            self.validate_action,
            self.build_action,
            self.export_action,
            self.settings_action,
        ):
            toolbar.addAction(action)

    def _build_central(self) -> None:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.project_tree = ProjectTree()
        self.console = BuildConsole()
        splitter.addWidget(self.project_tree)
        splitter.addWidget(self.console)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([250, 850])
        self.setCentralWidget(splitter)

    def _build_status(self) -> None:
        self.stage_label = QtWidgets.QLabel("READY")
        self.statusBar().addWidget(self.stage_label)
        self.statusBar().addPermanentWidget(QtWidgets.QLabel("v3.0.0-beta.1"))

    def _apply_stage(self, stage: BuildStage, progress: int, message: str) -> None:
        self.state.set_stage(stage, progress, message)
        self.stage_label.setText(stage.value.upper())
        self.console.set_progress(progress)
        self.console.write(message)

    def open_project(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open PP-AIPP project")
        if not path:
            return
        resolved = self.state.open_project(path)
        self.project_tree.load_project(resolved.name)
        self.stage_label.setText(self.state.stage.value.upper())
        self.console.set_progress(self.state.progress)
        self.console.write(self.state.messages[-1])

    def import_gold_master(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Gold Master",
            "",
            "Word documents (*.docx);;All files (*)",
        )
        if not path:
            return
        resolved = self.state.select_gold_master(path)
        self.stage_label.setText(self.state.stage.value.upper())
        self.console.set_progress(self.state.progress)
        self.console.write(f"Selected controlled source: {resolved.name}")
        self.console.write("Parser execution will be connected in Beta B1.2.")

    def validate_project(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        self._apply_stage(BuildStage.VALIDATING, 35, "Validation requested.")
        self.console.write("Verification pipeline connection is scheduled for Beta B1.3.")
        self._apply_stage(BuildStage.READY, 40, "Validation command prepared.")

    def build_book(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        if not self.state.gold_master_path:
            self._warn("Select a Gold Master first.")
            return
        self._apply_stage(BuildStage.BUILDING, 55, "Build Book requested.")
        self.console.write("Database-driven Layout Engine will be connected in Beta B1.3.")
        self._apply_stage(BuildStage.READY, 60, "Build command prepared.")

    def export_book(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        self._apply_stage(BuildStage.EXPORTING, 75, "Export requested.")
        self.console.write("Export Engine integration is scheduled for Beta B2.")
        self._apply_stage(BuildStage.READY, 80, "Export command prepared.")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.state.export_path, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.console.write(f"Export folder: {dialog.export_path.text()}")

    def _warn(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(self, "PP-AIPP", text)
        self.console.write(f"WARNING: {text}")
