from pathlib import Path


def test_desktop_modules_are_packaged():
    root = Path(__file__).parents[1] / "src" / "pp_aipp" / "desktop"
    expected = {
        "__init__.py",
        "app.py",
        "main_window.py",
        "qt.py",
        "settings_dialog.py",
        "state.py",
        "theme.py",
        "widgets.py",
    }
    assert expected.issubset({p.name for p in root.iterdir()})


def test_pyproject_declares_desktop_extra():
    text = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert 'desktop = ["PySide6>=6.7,<7"]' in text
    assert 'pp-aipp-desktop = "pp_aipp.desktop.app:main"' in text
