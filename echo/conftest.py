from __future__ import absolute_import, division, print_function

qapp = None


def get_qapp():
    global qapp
    from qtpy import QtWidgets
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication([''])
    return qapp


def pytest_configure(config):

    try:
        from qtpy import QtWidgets  # noqa
    except ImportError:
        pass
    else:
        app = get_qapp()  # noqa
