__all__ = [
    "PYQT5_INSTALLED", "PYQT6_INSTALLED",
    "PYSIDE2_INSTALLED", "PYSIDE6_INSTALLED",
    "QTPY_INSTALLED", "QT_INSTALLED",
    "SKIP_QT_TEST"
]


def package_installed(package):
    from importlib.util import find_spec
    return find_spec(package) is not None


PYQT5_INSTALLED = package_installed("PyQt5")
PYQT6_INSTALLED = package_installed("PyQt6")
PYSIDE2_INSTALLED = package_installed("PySide2")
PYSIDE6_INSTALLED = package_installed("PySide6")
QTPY_INSTALLED = package_installed("qtpy")
QT_INSTALLED = PYQT5_INSTALLED or PYQT6_INSTALLED or PYSIDE2_INSTALLED or PYSIDE6_INSTALLED
SKIP_QT_TEST = not (QTPY_INSTALLED and QT_INSTALLED)
