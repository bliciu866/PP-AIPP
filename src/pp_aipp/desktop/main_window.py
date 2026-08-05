from __future__ import annotations

import os

from pp_aipp.ai_photography import application_dir, default_local_python
from pp_aipp.build_pipeline import build_gold_master_book
from pp_aipp.export_engine import export_book_package
from pp_aipp.gold_master import GoldMasterProject
from pp_aipp.photography import import_photo_assets, prepare_next_photo_batch

from .ai_photo_worker import AIPhotoWorker
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
        self._ai_thread = None
        self._ai_worker = None
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

        self.photos_action = QtGui.QAction("Import Photos", self)
        self.photos_action.triggered.connect(self.import_photos)

        self.plan_photos_action = QtGui.QAction("Prepare Photo Batch", self)
        self.plan_photos_action.triggered.connect(self.prepare_photo_batch)

        self.generate_photos_action = QtGui.QAction("Generate AI Photos", self)
        self.generate_photos_action.triggered.connect(self.generate_ai_photos)

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
        tools_menu.addAction(self.photos_action)
        tools_menu.addAction(self.plan_photos_action)
        tools_menu.addAction(self.generate_photos_action)
        tools_menu.addAction(self.settings_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        for action in (
            self.open_project_action,
            self.import_action,
            self.validate_action,
            self.build_action,
            self.photos_action,
            self.plan_photos_action,
            self.generate_photos_action,
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
        self.statusBar().addPermanentWidget(QtWidgets.QLabel("v3.0.0-beta.6 / B2.8"))

    def generate_ai_photos(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        if not (self.state.project_path / "data" / "project.sqlite3").is_file():
            self._warn("Build the book first so the recipe database is available.")
            return
        backend, accepted = QtWidgets.QInputDialog.getItem(
            self,
            "AI Photography Engine",
            "Choose the image generator:",
            ["Local Free AI (no API cost)", "OpenAI Images API (paid)"],
            0,
            False,
        )
        if not accepted:
            return
        provider = "local" if str(backend).startswith("Local") else "openai"
        api_key = ""
        if provider == "local" and not default_local_python().is_file():
            QtWidgets.QMessageBox.information(
                self,
                "Install Local Free AI",
                "Local Free AI needs one-time setup.\n\n"
                "Run SETUP_LOCAL_AI.bat from the PP-AIPP application folder, then return here.\n"
                "The setup and model are free, but the first download is several GB.",
            )
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(application_dir())))
            return
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if provider == "openai" and not api_key:
            api_key, accepted = QtWidgets.QInputDialog.getText(
                self,
                "OpenAI API Key",
                "Paste your OpenAI API key. It is used only for this run and is not saved:",
                QtWidgets.QLineEdit.EchoMode.Password,
            )
            if not accepted or not api_key.strip():
                return
            api_key = api_key.strip()
        batch_size, accepted = QtWidgets.QInputDialog.getInt(
            self, "AI Photography Campaign", "Maximum photos to generate:", 80, 1, 80,
        )
        if not accepted:
            return
        quality, accepted = QtWidgets.QInputDialog.getItem(
            self,
            "AI Photography Quality",
            "Image quality (higher quality takes longer locally):",
            ["low", "medium", "high"],
            0,
            False,
        )
        if not accepted:
            return
        answer = QtWidgets.QMessageBox.question(
            self,
            "Start AI Photography Campaign",
            f"Generate up to {batch_size} missing recipe photos at {quality} quality?\n\n"
            + ("Local Free AI uses your computer and has no API charge. " if provider == "local"
               else "The OpenAI Images API is billed to your API account. ")
            + "Existing PP-Rxxx photos will be skipped, and an interrupted campaign can be resumed.",
        )
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        self.generate_photos_action.setEnabled(False)
        self.console.set_progress(1)
        self.console.write("Starting resumable AI photography campaign...")
        self._ai_thread = QtCore.QThread(self)
        self._ai_worker = AIPhotoWorker(
            self.state.project_path, api_key, batch_size, str(quality), provider,
        )
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.run)
        self._ai_worker.progress.connect(self._on_ai_photo_progress)
        self._ai_worker.finished.connect(self._on_ai_photo_finished)
        self._ai_worker.failed.connect(self._on_ai_photo_failed)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.failed.connect(self._ai_thread.quit)
        self._ai_thread.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)
        self._ai_thread.finished.connect(self._on_ai_photo_cleanup)
        self._ai_thread.start()

    @QtCore.Slot(int, str)
    def _on_ai_photo_progress(self, progress: int, message: str) -> None:
        self.console.set_progress(progress)
        self.console.write(message)

    @QtCore.Slot(object)
    def _on_ai_photo_finished(self, result) -> None:
        self.console.set_progress(100)
        self.console.write(f"AI photos generated: {result.generated}")
        self.console.write(f"Existing photos skipped: {result.skipped}")
        self.console.write(f"Generation failures: {result.failed}")
        self.console.write(f"Missing recipe photos: {result.remaining}")
        self.console.write(f"Campaign coverage: {result.coverage_percent}%")
        self.console.write(f"Campaign report: {result.report_path}")
        QtWidgets.QMessageBox.information(
            self,
            "PP-AIPP AI Photography Complete",
            f"Generated: {result.generated}\nFailed: {result.failed}\n"
            f"Remaining: {result.remaining}\nCoverage: {result.coverage_percent}%\n\n"
            f"Images saved to:\n{result.images_dir}",
        )

    @QtCore.Slot(str)
    def _on_ai_photo_failed(self, message: str) -> None:
        self.console.set_progress(0)
        self.console.write(f"AI photography campaign failed: {message}")
        self._warn(message)

    @QtCore.Slot()
    def _on_ai_photo_cleanup(self) -> None:
        self.generate_photos_action.setEnabled(True)
        self._ai_worker = None
        self._ai_thread = None

    def prepare_photo_batch(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        batch_size, accepted = QtWidgets.QInputDialog.getInt(
            self, "Prepare Photo Batch", "Number of missing recipes:", 10, 1, 80,
        )
        if not accepted:
            return
        try:
            plan = prepare_next_photo_batch(self.state.project_path, batch_size=batch_size)
            self.console.write(f"Prepared photography batch: {plan.batch_number}")
            self.console.write(f"Recipes: {', '.join(plan.recipe_ids)}")
            self.console.write(f"Batch folder: {plan.batch_dir}")
            QtWidgets.QMessageBox.information(
                self,
                "PP-AIPP Photo Batch Ready",
                f"Batch: {plan.batch_number}\nRecipes: {len(plan.recipe_ids)}\n"
                f"Missing before batch: {plan.missing_total}\n"
                f"Coverage: {plan.coverage_percent}%\n\nSaved to:\n{plan.batch_dir}",
            )
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(plan.batch_dir)))
        except (OSError, ValueError) as exc:
            self._warn(str(exc))

    def import_photos(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select recipe photos folder")
        if not folder:
            return
        try:
            self.console.write("Importing and validating photography assets...")
            result = import_photo_assets(self.state.project_path, folder)
            self.console.write(f"Imported photos: {result.imported}")
            self.console.write(f"Automatically prepared to 4:5: {result.auto_prepared}")
            self.console.write(f"Replaced existing photos: {result.replaced}")
            self.console.write(f"Production ready: {result.ready}")
            self.console.write(f"Need crop / resolution review: {result.needs_crop}")
            self.console.write(f"Missing recipe photos: {result.missing}")
            self.console.write(f"Campaign coverage: {result.coverage_percent}%")
            self.console.write(f"Completed photography batch: {result.batch_number}")
            if result.next_missing:
                self.console.write(f"Next missing: {', '.join(result.next_missing)}")
            self.console.write(f"Photography report: {result.report_path}")
            QtWidgets.QMessageBox.information(
                self,
                "PP-AIPP Photography Import",
                f"Imported: {result.imported}\nReady: {result.ready}\n"
                f"Auto-prepared: {result.auto_prepared}\nReplaced: {result.replaced}\n"
                f"Needs attention: {result.needs_crop}\nMissing: {result.missing}\n\n"
                f"Coverage: {result.coverage_percent}%\nBatch: {result.batch_number}\n"
                f"Next missing: {', '.join(result.next_missing) or 'None'}\n\n"
                f"Saved to: {result.images_dir}",
            )
        except (OSError, ValueError) as exc:
            self._warn(str(exc))

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
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Gold Master",
            "",
            "Word documents (*.docx);;All files (*)",
        )
        if not path:
            return
        try:
            self._apply_stage(BuildStage.IMPORTING, 10, "Importing controlled source...")
            result = GoldMasterProject(self.state.project_path).import_source(path)
            self.state.gold_master_path = result.imported_source
            self._apply_stage(BuildStage.READY, 20, f"Imported: {result.imported_source.name}")
            self.console.write(f"SHA-256: {result.manifest.source_sha256}")
            self.console.write("Gold Master structure validated.")
        except (OSError, ValueError) as exc:
            self._apply_stage(BuildStage.FAILED, 0, f"Import failed: {exc}")
            self._warn(str(exc))

    def validate_project(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        self._apply_stage(BuildStage.VALIDATING, 35, "Validating Gold Master project...")
        result = GoldMasterProject(self.state.project_path).validate()
        if result.valid:
            self._apply_stage(BuildStage.READY, 40, "Gold Master project is valid.")
            return
        for issue in result.issues:
            self.console.write(f"{issue.code}: {issue.message}")
        self._apply_stage(BuildStage.FAILED, 0, "Gold Master validation failed.")

    def build_book(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        if not self.state.gold_master_path:
            self._warn("Select a Gold Master first.")
            return
        try:
            self._apply_stage(BuildStage.BUILDING, 50, "Parsing Gold Master...")
            QtWidgets.QApplication.processEvents()
            result = build_gold_master_book(
                self.state.project_path,
                self.state.gold_master_path,
            )
            self.console.set_progress(75)
            self.console.write(
                f"Imported {result.import_summary.imported_recipes} recipes and "
                f"{result.import_summary.ingredients} ingredients."
            )
            self.console.write(f"Database: {result.database_path}")
            self.console.write(f"QA report: {result.layout_report_path}")
            self.console.write(f"Built book: {result.layout.output_docx}")
            self.console.write(
                f"Content coverage: {result.import_summary.method_steps} method steps; "
                f"{result.import_summary.warnings} source warnings."
            )
            self.state.built_book_path = result.layout.output_docx
            self.state.export_path = self.state.project_path / "exports"
            self._apply_stage(
                BuildStage.COMPLETE,
                80,
                f"Book built: {result.layout.output_docx.name}",
            )
            self._show_build_complete(result.layout.output_docx, result.layout.recipe_count)
        except (OSError, ValueError) as exc:
            self._apply_stage(BuildStage.FAILED, 0, f"Build failed: {exc}")
            self._warn(str(exc))

    def export_book(self) -> None:
        if not self.state.project_path:
            self._warn("Open a project first.")
            return
        if not self.state.built_book_path:
            candidate = self.state.project_path / "build" / "Project_Physique_30_Days_Fat_Loss_Built.docx"
            if candidate.is_file():
                self.state.built_book_path = candidate
            else:
                self._warn("Build the book before exporting.")
                return
        try:
            self._apply_stage(BuildStage.EXPORTING, 85, "Creating verified export package...")
            QtWidgets.QApplication.processEvents()
            result = export_book_package(self.state.project_path, self.state.built_book_path)
            self.state.export_path = result.export_dir
            self.console.write(f"Exported book: {result.book_path}")
            self.console.write(f"Print PDF: {result.pdf_path}")
            self.console.write(f"Publishing guide: {result.publishing_readme_path}")
            self.console.write(f"Image coverage: {result.image_coverage_path}")
            self.console.write(f"Export manifest: {result.manifest_path}")
            self.console.write(f"Export package: {result.package_path}")
            self._apply_stage(BuildStage.COMPLETE, 100, "Export package complete.")
            self._show_export_complete(result.package_path, result.file_count)
        except (OSError, ValueError) as exc:
            self._apply_stage(BuildStage.FAILED, 0, f"Export failed: {exc}")
            self._warn(str(exc))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.state.export_path, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.console.write(f"Export folder: {dialog.export_path.text()}")

    def _show_build_complete(self, output_path, recipe_count: int) -> None:
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("PP-AIPP Build Complete")
        box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        box.setText(f"Built {recipe_count} recipes.")
        box.setInformativeText(f"Saved to:\n{output_path}")
        open_book = box.addButton("Open Book", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        open_folder = box.addButton("Open Folder", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        box.addButton(QtWidgets.QMessageBox.StandardButton.Close)
        box.exec()
        clicked = box.clickedButton()
        if clicked is open_book:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(output_path)))
        elif clicked is open_folder:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(output_path.parent)))

    def _show_export_complete(self, package_path, file_count: int) -> None:
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("PP-AIPP Export Complete")
        box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        box.setText(f"Exported {file_count} verified files.")
        box.setInformativeText(f"Package saved to:\n{package_path}")
        open_export = box.addButton("Open Export", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        open_folder = box.addButton("Open Folder", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        box.addButton(QtWidgets.QMessageBox.StandardButton.Close)
        box.exec()
        clicked = box.clickedButton()
        if clicked is open_export:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(package_path)))
        elif clicked is open_folder:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(package_path.parent)))

    def _warn(self, text: str) -> None:
        QtWidgets.QMessageBox.warning(self, "PP-AIPP", text)
        self.console.write(f"WARNING: {text}")
