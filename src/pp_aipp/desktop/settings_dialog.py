from __future__ import annotations

from pathlib import Path

from .qt import QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, export_path: Path | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PP-AIPP Settings")
        self.resize(480, 220)
        form = QtWidgets.QFormLayout(self)

        self.language = QtWidgets.QComboBox()
        self.language.addItems(["English (UK)", "Polski"])
        form.addRow("Interface language", self.language)

        self.book_format = QtWidgets.QComboBox()
        self.book_format.addItems(['8.5 × 11 in', 'A4', '6 × 9 in'])
        form.addRow("Default book format", self.book_format)

        self.export_path = QtWidgets.QLineEdit(str(export_path or "exports"))
        browse = QtWidgets.QPushButton("Browse…")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.export_path)
        row.addWidget(browse)
        form.addRow("Export folder", row)
        browse.clicked.connect(self._browse)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select export folder")
        if path:
            self.export_path.setText(path)
