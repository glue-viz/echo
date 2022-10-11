import pytest
import numpy as np

from qtpy import QtWidgets
from qtpy.QtCore import Qt

from echo.core import CallbackProperty
from echo.selection import SelectionCallbackProperty, ChoiceSeparator
from echo.qt.connect import connect_list_selection


class Example(object):
    a = SelectionCallbackProperty(default_index=1)
    b = CallbackProperty()


def test_connect_list_selection():

    t = Example()

    a_prop = getattr(type(t), 'a')
    a_prop.set_choices(t, [4, 3.5])
    a_prop.set_display_func(t, lambda x: 'value: {0}'.format(x))

    list_widget = QtWidgets.QListWidget()

    c1 = connect_list_selection(t, 'a', list_widget)  # noqa

    assert list_widget.item(0).text() == 'value: 4'
    assert list_widget.item(1).text() == 'value: 3.5'
    assert list_widget.item(0).data(Qt.UserRole).data == 4
    assert list_widget.item(1).data(Qt.UserRole).data == 3.5

    list_widget.setCurrentItem(list_widget.item(1))
    assert t.a == 3.5

    list_widget.setCurrentItem(list_widget.item(0))
    assert t.a == 4

    list_widget.setCurrentItem(list_widget.item(-1))
    assert t.a is None

    t.a = 3.5
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(1)

    t.a = 4
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(0)

    with pytest.raises(ValueError) as exc:
        t.a = 2
    assert exc.value.args[0] == 'value 2 is not in valid choices: [4, 3.5]'

    t.a = None
    assert len(list_widget.selectedItems()) == 0

    # Changing choices should change Qt list_widget box. Let's first try with a case
    # in which there is a matching data value in the new list_widget box

    t.a = 3.5
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(1)

    a_prop.set_choices(t, (4, 5, 3.5))
    assert list_widget.count() == 3

    assert t.a == 3.5
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(2)

    assert list_widget.item(0).text() == 'value: 4'
    assert list_widget.item(1).text() == 'value: 5'
    assert list_widget.item(2).text() == 'value: 3.5'
    assert list_widget.item(0).data(Qt.UserRole).data == 4
    assert list_widget.item(1).data(Qt.UserRole).data == 5
    assert list_widget.item(2).data(Qt.UserRole).data == 3.5

    # Now we change the choices so that there is no matching data - in this case
    # the index should change to that given by default_index

    a_prop.set_choices(t, (4, 5, 6))

    assert t.a == 5
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(1)
    assert list_widget.count() == 3

    assert list_widget.item(0).text() == 'value: 4'
    assert list_widget.item(1).text() == 'value: 5'
    assert list_widget.item(2).text() == 'value: 6'
    assert list_widget.item(0).data(Qt.UserRole).data == 4
    assert list_widget.item(1).data(Qt.UserRole).data == 5
    assert list_widget.item(2).data(Qt.UserRole).data == 6

    # Finally, if there are too few choices for the default_index to be valid,
    # pick the last item in the list_widget

    a_prop.set_choices(t, (9,))

    assert t.a == 9
    assert len(list_widget.selectedItems()) == 1
    assert list_widget.selectedItems()[0] is list_widget.item(0)
    assert list_widget.count() == 1

    assert list_widget.item(0).text() == 'value: 9'
    assert list_widget.item(0).data(Qt.UserRole).data == 9

    # Now just make sure that ChoiceSeparator works

    separator = ChoiceSeparator('header')
    a_prop.set_choices(t, (separator, 1, 2))

    assert list_widget.count() == 3
    assert list_widget.item(0).text() == 'header'
    assert list_widget.item(0).data(Qt.UserRole).data is separator

    # And setting choices to an empty iterable shouldn't cause issues

    a_prop.set_choices(t, ())
    assert list_widget.count() == 0

    # Try including an array in the choices
    a_prop.set_choices(t, (4, 5, np.array([1, 2, 3])))


def test_connect_list_widget_selection_invalid():

    t = Example()

    list_widget = QtWidgets.QListWidget()

    with pytest.raises(TypeError) as exc:
        connect_list_selection(t, 'b', list_widget)
    assert exc.value.args[0] == 'connect_list_selection requires a SelectionCallbackProperty'
