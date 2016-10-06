from __future__ import absolute_import, division, print_function

import pytest

try:
    from qtpy import QtWidgets
except ImportError:
    QTPY_INSTALLED = False
else:
    QTPY_INSTALLED = True

from echo import CallbackProperty
from echo.qt.connect import (connect_checkable_button, connect_text,
                             connect_combo_data, connect_combo_text,
                             connect_float_text, connect_value)


@pytest.mark.skipif("not QTPY_INSTALLED")
def test_connect_checkable_button():

    class Test(object):
        a = CallbackProperty()

    t = Test()

    box = QtWidgets.QCheckBox()
    connect_checkable_button(t, 'a', box)

    box.setChecked(True)
    assert t.a

    box.setChecked(False)
    assert not t.a

    t.a = True
    assert box.isChecked()

    t.a = False
    assert not box.isChecked()


@pytest.mark.skipif("not QTPY_INSTALLED")
def test_connect_text():

    class Test(object):
        a = CallbackProperty()
        b = CallbackProperty()

    t = Test()

    box = QtWidgets.QLineEdit()
    connect_text(t, 'a', box)

    label = QtWidgets.QLabel()
    connect_text(t, 'b', label)

    box.setText('test1')
    box.editingFinished.emit()
    assert t.a == 'test1'

    t.a = 'test3'
    assert box.text() == 'test3'

    t.b = 'test4'
    assert label.text() == 'test4'


@pytest.mark.skipif("not QTPY_INSTALLED")
def test_connect_combo():

    class Test(object):
        a = CallbackProperty()
        b = CallbackProperty()

    t = Test()

    combo = QtWidgets.QComboBox()
    combo.addItem('label1', 4)
    combo.addItem('label2', 3.5)

    connect_combo_text(t, 'a', combo)
    connect_combo_data(t, 'b', combo)

    combo.setCurrentIndex(1)
    assert t.a == 'label2'
    assert t.b == 3.5

    combo.setCurrentIndex(0)
    assert t.a == 'label1'
    assert t.b == 4

    combo.setCurrentIndex(-1)
    assert t.a is None
    assert t.b is None

    t.a = 'label2'
    assert combo.currentIndex() == 1

    t.a = 'label1'
    assert combo.currentIndex() == 0

    with pytest.raises(ValueError) as exc:
        t.a = 'label3'
    assert exc.value.args[0] == 'label3 not found in combo box'

    t.a = None
    assert combo.currentIndex() == -1

    t.b = 3.5
    assert combo.currentIndex() == 1

    t.b = 4
    assert combo.currentIndex() == 0

    with pytest.raises(ValueError) as exc:
        t.b = 2
    assert exc.value.args[0] == '2 not found in combo box'

    t.b = None
    assert combo.currentIndex() == -1


@pytest.mark.skipif("not QTPY_INSTALLED")
def test_connect_float_text():

    class Test(object):
        a = CallbackProperty()
        b = CallbackProperty()
        c = CallbackProperty()

    t = Test()

    line1 = QtWidgets.QLineEdit()
    line2 = QtWidgets.QLineEdit()
    line3 = QtWidgets.QLabel()

    def fmt_func(x):
        return str(int(round(x)))

    connect_float_text(t, 'a', line1)
    connect_float_text(t, 'b', line2, fmt="{:5.2f}")
    connect_float_text(t, 'c', line3, fmt=fmt_func)

    for line in (line1, line2):

        line1.setText('1.0')
        line1.editingFinished.emit()
        assert t.a == 1.0

        line1.setText('banana')
        line1.editingFinished.emit()
        assert t.a == 0.0

    t.a = 3.
    assert line1.text() == '3'

    t.b = 5.211
    assert line2.text() == ' 5.21'

    t.c = -2.222
    assert line3.text() == '-2'


@pytest.mark.skipif("not QTPY_INSTALLED")
def test_connect_value():

    class Test(object):
        a = CallbackProperty()
        b = CallbackProperty()
        c = CallbackProperty()

    t = Test()

    slider = QtWidgets.QSlider()
    slider.setMinimum(0)
    slider.setMaximum(100)

    connect_value(t, 'a', slider)
    connect_value(t, 'b', slider, value_range=(0, 10))

    with pytest.raises(Exception) as exc:
        connect_value(t, 'c', slider, log=True)
    assert exc.value.args[0] == "log option can only be set if value_range is given"

    connect_value(t, 'c', slider, value_range=(0.01, 100), log=True)

    slider.setValue(25)
    assert t.a == 25
    assert t.b == 2.5
    assert t.c == 0.1

    t.a = 30
    assert slider.value() == 30

    t.b = 8.5
    assert slider.value() == 85

    t.c = 10
    assert slider.value() == 75
