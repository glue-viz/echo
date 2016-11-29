from __future__ import absolute_import, division, print_function

import pytest
from mock import MagicMock

from echo import CallbackProperty, ListCallbackProperty, HasCallbackProperties


class Stub(HasCallbackProperties):
    prop1 = ListCallbackProperty()
    prop2 = ListCallbackProperty()


def test_list_normal_callback():

    stub = Stub()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = [3]
    assert test1.call_count == 1

    stub.prop2 = [4]
    assert test1.call_count == 1


def test_list_invalid():

    stub = Stub()
    with pytest.raises(TypeError) as exc:
        stub.prop1 = 'banana'
    assert exc.value.args[0] == "callback property should be a list"


def test_list_default():

    stub = Stub()
    stub.prop1.append(1)


def test_list_change_callback():

    stub = Stub()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    assert test1.call_count == 0

    stub.prop1.append(3)
    assert test1.call_count == 1
    assert stub.prop1 == [3]

    stub.prop1.clear()
    assert test1.call_count == 2
    assert stub.prop1 == []

    stub.prop1.extend([1, 2, 3])
    assert test1.call_count == 3
    assert stub.prop1 == [1, 2, 3]

    stub.prop1.insert(0, -1)
    assert test1.call_count == 4
    assert stub.prop1 == [-1, 1, 2, 3]

    p = stub.prop1.pop()
    assert test1.call_count == 5
    assert p == 3
    assert stub.prop1 == [-1, 1, 2]

    stub.prop1.remove(1)
    assert test1.call_count == 6
    assert stub.prop1 == [-1, 2]

    stub.prop1.reverse()
    assert test1.call_count == 7
    assert stub.prop1 == [2, -1]

    stub.prop1.sort()
    assert test1.call_count == 8
    assert stub.prop1 == [-1, 2]


class Simple(HasCallbackProperties):
    a = CallbackProperty()


def test_nested_callbacks_in_list():

    stub1 = Stub()
    stub2 = Stub()
    simple = Simple()
    stub1.prop1.append(stub2)
    stub1.prop1.append(simple)

    test1 = MagicMock()

    stub1.add_callback('prop1', test1)

    stub2.prop1.append(2)
    assert test1.call_count == 1

    simple.a = 'banana!'
    assert test1.call_count == 2
