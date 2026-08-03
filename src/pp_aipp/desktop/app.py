from __future__ import annotations

import sys

from ..core.kernel import Kernel
from .qt import QtWidgets
from .main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    app = QtWidgets.QApplication(argv or sys.argv)
    app.setApplicationName("PP-AIPP")
    app.setOrganizationName("Project Physique")

    kernel = Kernel("config/default.yaml")
    kernel.start()
    window = MainWindow(kernel)
    window.show()
    try:
        return app.exec()
    finally:
        kernel.stop()


if __name__ == "__main__":
    raise SystemExit(main())
