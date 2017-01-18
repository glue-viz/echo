from __future__ import absolute_import, division, print_function

import sys
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

    if sys.version_info[0] == 2:
        stub.prop1[:] = []
    else:
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

    stub.prop1[0] = 3
    assert test1.call_count == 9
    assert stub.prop1 == [3, 2]

    stub.prop1[:] = []
    assert test1.call_count == 10
    assert stub.prop1 == []


class Simple(HasCallbackProperties):
    a = CallbackProperty()


def test_state_in_a_list():

    stub = Stub()

    state1 = Simple()
    state2 = Simple()
    state3 = Simple()
    state4 = Simple()
    state5 = Simple()

    # Add three of the state objects to the list in different ways
    stub.prop1.append(state1)
    stub.prop1.extend([state2, 3.4])
    stub.prop1.insert(1, state3)
    stub.prop1[3] = state4

    # Check that all states except state 4 have a callback added
    prop = getattr(Simple, 'a')
    assert len(prop._callbacks[state1]) == 1
    assert len(prop._callbacks[state2]) == 1
    assert len(prop._callbacks[state3]) == 1
    assert len(prop._callbacks[state4]) == 1
    assert state5 not in prop._callbacks

    # Add a callback to the main list
    callback = MagicMock()
    stub.add_callback('prop1', callback)

    # Check that modifying attributes of the state objects triggers the list
    # callback.
    assert callback.call_count == 0
    state1.a = 1
    assert callback.call_count == 1
    state2.a = 1
    assert callback.call_count == 2
    state3.a = 1
    assert callback.call_count == 3
    state4.a = 1
    assert callback.call_count == 4
    state5.a = 1
    assert callback.call_count == 4

    # Remove one of the state objects and try again
    stub.prop1.pop(0)
    assert callback.call_count == 5
    assert len(prop._callbacks[state1]) == 0
    assert len(prop._callbacks[state2]) == 1
    assert len(prop._callbacks[state3]) == 1
    assert len(prop._callbacks[state4]) == 1
    assert state5 not in prop._callbacks

    # Now modifying state1 sholdn't affect the call cont
    state1.a = 2
    assert callback.call_count == 5
    state2.a = 2
    assert callback.call_count == 6
    state3.a = 2
    assert callback.call_count == 7
    state4.a = 2
    assert callback.call_count == 8
    state5.a = 2
    assert callback.call_count == 8

    # Remove again this time using remove
    stub.prop1.remove(state2)
    assert callback.call_count == 9
    assert len(prop._callbacks[state1]) == 0
    assert len(prop._callbacks[state2]) == 0
    assert len(prop._callbacks[state3]) == 1
    assert len(prop._callbacks[state4]) == 1
    assert state5 not in prop._callbacks

    # Now modifying state2 sholdn't affect the call cont
    state1.a = 3
    assert callback.call_count == 9
    state2.a = 3
    assert callback.call_count == 9
    state3.a = 3
    assert callback.call_count == 10
    state4.a = 3
    assert callback.call_count == 11
    state5.a = 3
    assert callback.call_count == 11

    # Remove using item access
    stub.prop1[1] = 3.3
    assert callback.call_count == 12
    assert len(prop._callbacks[state1]) == 0
    assert len(prop._callbacks[state2]) == 0
    assert len(prop._callbacks[state3]) == 1
    assert len(prop._callbacks[state4]) == 0
    assert state5 not in prop._callbacks

    # Now modifying state4 sholdn't affect the call cont
    state1.a = 4
    assert callback.call_count == 12
    state2.a = 4
    assert callback.call_count == 12
    state3.a = 4
    assert callback.call_count == 13
    state4.a = 4
    assert callback.call_count == 13
    state5.a = 4
    assert callback.call_count == 13

    # Now use slice access to remove state3 and add state5 in one go
    stub.prop1[0:2] = [2.2, state5]
    assert callback.call_count == 14
    assert len(prop._callbacks[state1]) == 0
    assert len(prop._callbacks[state2]) == 0
    assert len(prop._callbacks[state3]) == 0
    assert len(prop._callbacks[state4]) == 0
    assert len(prop._callbacks[state5]) == 1

    # Now only modifying state5 should have an effect
    state1.a = 5
    assert callback.call_count == 14
    state2.a = 5
    assert callback.call_count == 14
    state3.a = 5
    assert callback.call_count == 14
    state4.a = 5
    assert callback.call_count == 14
    state5.a = 5
    assert callback.call_count == 15

    if sys.version_info[0] >= 3:

        # On Python 3, check that clear does the right thing
        stub.prop1.clear()
        assert callback.call_count == 16
        assert len(prop._callbacks[state1]) == 0
        assert len(prop._callbacks[state2]) == 0
        assert len(prop._callbacks[state3]) == 0
        assert len(prop._callbacks[state4]) == 0
        assert len(prop._callbacks[state5]) == 0

        # Now the callback should never be called
        state1.a = 6
        assert callback.call_count == 16
        state2.a = 6
        assert callback.call_count == 16
        state3.a = 6
        assert callback.call_count == 16
        state4.a = 6
        assert callback.call_count == 16
        state5.a = 6
        assert callback.call_count == 16


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
