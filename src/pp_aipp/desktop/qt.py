from __future__ import annotations

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError as exc:  # pragma: no cover - depends on desktop extra
    raise RuntimeError(
        "PySide6 is required for the desktop application. "
        "Install with: pip install -e '.[desktop]'"
    ) from exc

__all__ = ["QtCore", "QtGui", "QtWidgets"]
