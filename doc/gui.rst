.. currentmodule:: echo.qt

Interfacing with Qt widgets
---------------------------

When designing GUIs, it can be useful to have class properties link directly
to widgets. Echo currently includes functions to connect to Qt widgets, which
are described below. Contributions for other GUI frameworks are welcome!

We recommend using Qt libraries via the `QtPy
<https://pypi.python.org/pypi/QtPy/>`_ package, which provides a uniform API to
PyQt4, PyQt5, and PySide, and we use this in the following examples.

Let's assume we have a simple Qt window with a single checkbox::

    from qtpy import QtWidgets

    class MySimpleWindow(QtWidgets.QMainWindow):

        def __init__(self, parent=None):
            super(MySimpleWindow, self).__init__(parent=parent)
            self.checkbox = QtWidgets.QCheckBox()

We can now add a callback property to the class and connect the property to the
Qt checkbox::

    from qtpy import QtWidgets
    from echo import CallbackProperty
    from echo.qt import connect_checkable_button

    class MySimpleWindow(QtWidgets.QMainWindow):

        active = CallbackProperty(True)

        def __init__(self, parent=None):
            super(MySimpleWindow, self).__init__(parent=parent)
            self.checkbox = QtWidgets.QCheckBox()
            self.setCentralWidget(self.checkbox)
            self._connection = connect_checkable_button(self, 'active', self.checkbox)

Note that the connection object needs to be stored in a variable, as one there
are no references left to the connection object, the connection is removed.

Let's now write a small script that uses this Qt window and adds a callback
when ``active`` is changed::

    from echo import add_callback

    def toggled(new):
        print("Checkbox toggled: %s" % new)

    app = QtWidgets.QApplication([''])
    window = MySimpleWindow()
    window.show()

    add_callback(window, 'active', toggled)

    app.exec_()

If you run this script, and click on the checkbox multiple times, the output
in the terminal will be::

    Checkbox toggled: False
    Checkbox toggled: True
    Checkbox toggled: False

In addition, if you need to access the value of the checkbox in the code, you
can now simply access ``window.active`` rather than
``window.checkbox.isChecked``.

A number of other functions are available to connect to other types of widgets,
including combo boxes and text fields - see the API documentation for the
:ref:`qtapi` for more details.
