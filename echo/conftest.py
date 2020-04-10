from __future__ import absolute_import, division, print_function

try:
    import qtpy  # noqa
except Exception:
    QT_INSTALLED = False
else:
    QT_INSTALLED = True

qapp = None


def get_qapp():
    global qapp
    from qtpy import QtWidgets
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication([''])
    return qapp


def pytest_configure(config):
    if QT_INSTALLED:
        from qtpy import QtWidgets  # noqa
        app = get_qapp()  # noqa


def pytest_unconfigure(config):
    if QT_INSTALLED:
        global qapp
        qapp.exit()
        qapp = None
