import pytest
from unittest.mock import MagicMock

from echo import (CallbackProperty,
                  ListCallbackProperty,
                  DictCallbackProperty,
                  HasCallbackProperties)


class StubList(HasCallbackProperties):
    prop1 = ListCallbackProperty()
    prop2 = ListCallbackProperty()


class StubDict(HasCallbackProperties):
    prop1 = DictCallbackProperty()
    prop2 = DictCallbackProperty()


class Simple(HasCallbackProperties):
    a = CallbackProperty()


def test_list_normal_callback():

    stub = StubList()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = [3]
    assert test1.call_count == 1

    stub.prop2 = [4]
    assert test1.call_count == 1


def test_list_invalid():

    stub = StubList()
    with pytest.raises(TypeError) as exc:
        stub.prop1 = 'banana'
    assert exc.value.args[0] == "callback property should be a list"


def test_list_default_empty():

    stub = StubList()
    stub.prop1.append(1)


def test_list_explicit_default():

    class TestList(HasCallbackProperties):
        prop = ListCallbackProperty(default=[1, 2, 3])

    test1 = TestList()
    assert test1.prop == [1, 2, 3]

    test2 = TestList()
    assert test2.prop == [1, 2, 3]

    test1.prop.append(4)
    assert test1.prop == [1, 2, 3, 4]
    assert test2.prop == [1, 2, 3]


def test_list_change_callback():

    stub = StubList()

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

    stub.prop1[0] = 3
    assert test1.call_count == 9
    assert stub.prop1 == [3, 2]

    stub.prop1[:] = []
    assert test1.call_count == 10
    assert stub.prop1 == []


def test_state_in_a_list():

    stub = StubList()

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

    # Check that all states except state 5 have a callback added
    assert len(state1._global_callbacks) == 1
    assert len(state2._global_callbacks) == 1
    assert len(state3._global_callbacks) == 1
    assert len(state4._global_callbacks) == 1
    assert len(state5._global_callbacks) == 0

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
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 1
    assert len(state3._global_callbacks) == 1
    assert len(state4._global_callbacks) == 1
    assert len(state5._global_callbacks) == 0

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
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 1
    assert len(state4._global_callbacks) == 1
    assert len(state5._global_callbacks) == 0

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
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 1
    assert len(state4._global_callbacks) == 0
    assert len(state5._global_callbacks) == 0

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
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 0
    assert len(state4._global_callbacks) == 0
    assert len(state5._global_callbacks) == 1

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

    # On Python 3, check that clear does the right thing
    stub.prop1.clear()
    assert callback.call_count == 16
    assert len(state1._global_callbacks) == 0
    assert len(state2._global_callbacks) == 0
    assert len(state3._global_callbacks) == 0
    assert len(state4._global_callbacks) == 0
    assert len(state5._global_callbacks) == 0

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


def test_list_nested_callbacks():

    stub1 = StubList()
    stub2 = StubList()
    simple = Simple()
    stub1.prop1.append(stub2)
    stub1.prop1.append(simple)

    test1 = MagicMock()

    stub1.add_callback('prop1', test1)

    stub2.prop1.append(2)
    assert test1.call_count == 1

    simple.a = 'banana!'
    assert test1.call_count == 2


def test_dict_normal_callback():

    stub = StubDict()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = {'a': 1}
    assert test1.call_count == 1

    stub.prop2 = {'b': 2}
    assert test1.call_count == 1


def test_dict_invalid():

    stub = StubDict()
    with pytest.raises(TypeError) as exc:
        stub.prop1 = 'banana'
    assert exc.value.args[0] == "Callback property should be a dictionary."


def test_dict_default_empty():

    stub = StubDict()
    stub.prop1['a'] = 1


def test_dict_explicit_default():

    class TestDict(HasCallbackProperties):
        prop = DictCallbackProperty(default={'a': 1, 'b': 2})

    test1 = TestDict()
    assert test1.prop == {'a': 1, 'b': 2}

    test2 = TestDict()
    assert test2.prop == {'a': 1, 'b': 2}

    test1.prop['c'] = 3
    assert test1.prop == {'a': 1, 'b': 2, 'c': 3}
    assert test2.prop == {'a': 1, 'b': 2}


def test_dict_change_callback():

    stub = StubDict()

    test1 = MagicMock()
    stub.add_callback('prop1', test1)

    assert test1.call_count == 0

    stub.prop1['a'] = 1
    assert test1.call_count == 1
    assert stub.prop1 == {'a': 1}

    stub.prop1.clear()
    assert test1.call_count == 2
    assert stub.prop1 == {}

    stub.prop1.update({'b': 2, 'c': 3, 'd': 4})
    assert test1.call_count == 3
    assert stub.prop1 == {'b': 2, 'c': 3, 'd': 4}

    p = stub.prop1.pop('b')
    assert test1.call_count == 4
    assert p == 2
    assert stub.prop1 == {'c': 3, 'd': 4}

    k, v = stub.prop1.popitem()
    assert test1.call_count == 5
    assert stub.prop1 == {'c': 3} if k == 'd' else {'d': 4}
    remaining_key = 'c' if k == 'd' else 'd'

    stub.prop1[remaining_key] = 6
    assert test1.call_count == 6
    assert stub.prop1 == {remaining_key: 6}

    stub.prop1.clear()
    assert test1.call_count == 7
    assert stub.prop1 == {}


def test_state_in_a_dict():

    stub = StubDict()

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


def test_dict_nested_callbacks():

    stub1 = StubDict()
    stub2 = StubDict()
    simple = Simple()
    stub1.prop1['a'] = stub2
    stub1.prop1['b'] = simple

    test1 = MagicMock()

    stub1.add_callback('prop1', test1)

    stub2.prop1['c'] = 2
    assert test1.call_count == 1

    simple.a = 'banana!'
    assert test1.call_count == 2


def test_multiple_nested_list_and_dict():

    stubd = StubDict()

    test1 = MagicMock()
    stubd.add_callback('prop1', test1)

    stubd.prop1 = {'a': {'b': {'c': 1}}}
    assert test1.call_count == 1

    stubd.prop1['a']['b']['c'] = 2
    assert test1.call_count == 2

    stubd.prop1['a']['b']['c'] = {'d': 3}
    assert test1.call_count == 3

    stubd.prop1['a']['b']['c']['d'] = 4
    assert test1.call_count == 4

    stubd.prop1['a']['b'] = [1, 2, 3]
    assert test1.call_count == 5

    stubd.prop1['a']['b'][1] = {'e': 6}
    assert test1.call_count == 6

    stubd.prop1['a']['b'][1]['e'] = 7
    assert test1.call_count == 7

    stubd.prop1['a'] = 2
    assert test1.call_count == 8

    stubl = StubList()

    test2 = MagicMock()
    stubl.add_callback('prop1', test2)

    stubl.prop1 = [1, 2, {'a': 3, 'b': [4, 5, {'c': 6}]}]
    assert test2.call_count == 1

    stubl.prop1[2]['b'][2]['c'] = 5
    assert test2.call_count == 2

    stubl.prop1[2]['b'][2] = {'d': 7}
    assert test2.call_count == 3

    stubl.prop1[2]['b'][2]['d'] = 2
    assert test2.call_count == 4

    stubl.prop1[2]['b'][2] = [1, 2]
    assert test2.call_count == 5

    stubl.prop1[2]['b'][2][0] = 3
    assert test2.call_count == 6

    stubl.prop1[2] = [1, 2]
    assert test2.call_count == 7

    stubl.prop1[2][1] = 3
    assert test2.call_count == 8


def test_list_additional_callbacks():

    stub = StubList()

    test1 = MagicMock()
    test2 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = [3]
    stub.prop2 = [4]

    assert test1.call_count == 1
    assert test2.call_count == 0

    stub.prop1.callbacks.append(test2)

    stub.prop2.append(5)
    assert test1.call_count == 1
    assert test2.call_count == 0

    stub.prop1.append(2)
    assert test1.call_count == 2
    assert test2.call_count == 1

    stub.prop1.callbacks.remove(test2)
    stub.prop1.append(4)
    assert test1.call_count == 3
    assert test2.call_count == 1


def test_dict_additional_callbacks():

    stub = StubDict()

    test1 = MagicMock()
    test2 = MagicMock()
    stub.add_callback('prop1', test1)

    stub.prop1 = {'a': 1}
    stub.prop2 = {'b': 2}

    assert test1.call_count == 1
    assert test2.call_count == 0

    stub.prop1.callbacks.append(test2)

    stub.prop2['c'] = 3
    assert test1.call_count == 1
    assert test2.call_count == 0

    stub.prop1['d'] = 4
    assert test1.call_count == 2
    assert test2.call_count == 1

    stub.prop1.callbacks.remove(test2)
    stub.prop1['e'] = 5
    assert test1.call_count == 3
    assert test2.call_count == 1
