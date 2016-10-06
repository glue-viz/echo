from __future__ import absolute_import, division, print_function

from qtpy import QtWidgets

qapp = None


def get_qapp():
    global qapp
    qapp = QtWidgets.QApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication([''])
    return qapp
