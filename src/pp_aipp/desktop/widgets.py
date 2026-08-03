from __future__ import annotations

from .qt import QtCore, QtWidgets


class ProjectTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Project Explorer")
        self.setMinimumWidth(230)
        self.show_empty()

    def show_empty(self) -> None:
        self.clear()
        root = QtWidgets.QTreeWidgetItem(["No project open"])
        self.addTopLevelItem(root)

    def load_project(self, name: str) -> None:
        self.clear()
        project = QtWidgets.QTreeWidgetItem([name])
        for label in ("Books", "Assets", "Images", "QA", "Exports", "Archive"):
            project.addChild(QtWidgets.QTreeWidgetItem([label]))
        self.addTopLevelItem(project)
        project.setExpanded(True)


class BuildConsole(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Build Console")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.clear_button.setMaximumWidth(90)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.clear_button)
        layout.addLayout(header)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Ready.")
        layout.addWidget(self.log, 1)
        self.clear_button.clicked.connect(self.log.clear)

    def write(self, message: str) -> None:
        self.log.appendPlainText(message)
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log.setTextCursor(cursor)

    def set_progress(self, value: int) -> None:
        self.progress.setValue(value)
