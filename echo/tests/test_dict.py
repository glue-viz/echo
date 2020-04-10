import pytest
from unittest.mock import MagicMock

from echo import CallbackProperty, DictCallbackProperty, HasCallbackProperties


class Stub(HasCallbackProperties):
    prop1 = DictCallbackProperty()
    prop2 = DictCallbackProperty()


def test_dict_normal_callback():

    stub = Stub()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = {'a': 1}
    assert test1.call_count == 1

    stub.prop2 = {'b': 2}
    assert test1.call_count == 1


def test_dict_invalid():

    stub = Stub()
    with pytest.raises(TypeError) as exc:
        stub.prop1 = 'banana'
    assert exc.value.args[0] == "Callback property should be a dictionary."


def test_dict_default():

    stub = Stub()
    stub.prop1['a'] = 1


def test_dict_change_callback():

    stub = Stub()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    assert test1.call_count == 0

    stub.prop1['a'] = 1
    assert test1.call_count == 1
    assert stub.prop1 == {'a': 1}

    stub.prop1.clear()
    assert test1.call_count == 2
    assert stub.prop1 == {}

    stub.prop1.update({'b': 2, 'c': 3})
    assert test1.call_count == 3
    assert stub.prop1 == {'b': 2, 'c': 3}

    p = stub.prop1.pop('b')
    assert test1.call_count == 4
    assert p == 2
    assert stub.prop1 == {'c': 3}

    stub.prop1['c'] = 4
    assert test1.call_count == 5
    assert stub.prop1 == {'c': 4}

    stub.prop1.clear()
    assert test1.call_count == 6
    assert stub.prop1 == {}


class Simple(HasCallbackProperties):
    a = CallbackProperty()


def test_state_in_a_dict():

    stub = Stub()

    state1 = Simple()
    state2 = Simple()
    state3 = Simple()

    # Add three of the state objects to the dict in different ways
    stub.prop1['a'] = state1
    stub.prop1.update({'b': state2})

    # Check that all states except state 3 have a callback added
    assert len(state1._global_callbacks) == 1
    assert len(state2._global_callbacks) == 1
    assert len(state3._global_callbacks) == 0

    # Add a callback to the main dict
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
    assert callback.call_count == 2

    # Remove one of the state objects and try again
    stub.prop1.pop('a')
    assert callback.call_count == 3
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 1
    assert len(state3._global_callbacks) == 0

    # Now modifying state1 sholdn't affect the call count
    state1.a = 2
    assert callback.call_count == 3
    state2.a = 2
    assert callback.call_count == 4
    state3.a = 2
    assert callback.call_count == 4

    # Remove using item access and add state3
    stub.prop1['b'] = 3.3
    stub.prop1['c'] = state3
    assert callback.call_count == 6
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 1

    # Now modifying state2 sholdn't affect the call cont
    state1.a = 4
    assert callback.call_count == 6
    state2.a = 4
    assert callback.call_count == 6
    state3.a = 4
    assert callback.call_count == 7

    # Check that clear does the right thing
    stub.prop1.clear()
    assert callback.call_count == 8
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 0

    # Now the callback should never be called
    state1.a = 6
    assert callback.call_count == 8
    state2.a = 6
    assert callback.call_count == 8
    state3.a = 6
    assert callback.call_count == 8


def test_nested_callbacks_in_list():

    stub1 = Stub()
    stub2 = Stub()
    simple = Simple()
    stub1.prop1['a'] = stub2
    stub1.prop1['b'] = simple

    test1 = MagicMock()

    stub1.add_callback('prop1', test1)

    stub2.prop1['c'] = 2
    assert test1.call_count == 1

    simple.a = 'banana!'
    assert test1.call_count == 2
