import pytest

from ..callback_container import CallbackContainer


def func_a():
    return 1


def func_b():
    return 2


class SimpleClass:

    def __init__(self, value):
        self._value = value

    def meth(self):
        return self._value


def test_callback_container_func():

    container = CallbackContainer()
    container.append(func_a)

    assert len(container) == 1
    assert func_a in container
    assert func_b not in container

    container.append(func_b)

    assert len(container) == 2
    assert func_a in container
    assert func_b in container

    callbacks = list(container)

    assert callbacks[0] is func_a
    assert callbacks[1] is func_b

    container.clear()

    assert len(container) == 0
    assert func_a not in container
    assert func_b not in container


def test_callback_container_meth():

    instance1 = SimpleClass(2)
    instance2 = SimpleClass(3)

    container = CallbackContainer()
    container.append(instance1.meth)

    assert len(container) == 1
    assert instance1.meth in container
    assert instance2.meth not in container

    container.append(instance2.meth)

    assert len(container) == 2
    assert instance1.meth in container
    assert instance2.meth in container

    callbacks = list(container)

    assert callbacks[0]() == 2
    assert callbacks[1]() == 3

    container.clear()

    assert len(container) == 0
    assert instance1.meth not in container
    assert instance2.meth not in container


def test_callback_container_invalid():

    container = CallbackContainer()
    with pytest.raises(TypeError, match=r'Only callable values can be stored in CallbackContainer'):
        container.append('banana')


def test_callback_container_duplicates():

    # Don't store duplicates

    instance1 = SimpleClass(2)
    instance2 = SimpleClass(3)

    container = CallbackContainer()
    container.append(func_a)
    container.append(instance1.meth)
    container.append(instance2.meth)
    container.append(instance1.meth)
    container.append(instance2.meth, priority=2)  # will be added as different priority
    container.append(func_a)
    container.append(instance2.meth)

    assert len(container) == 4
    assert func_a in container
    assert func_b not in container
    assert instance1.meth in container
    assert instance2.meth in container


def test_callback_container_remove():

    instance = SimpleClass(2)

    container = CallbackContainer()
    container.append(func_a)
    container.append(instance.meth)
    container.append(instance.meth, priority=2)

    assert len(container) == 3

    container.remove(instance.meth)

    assert len(container) == 1

    container.remove(func_a)

    assert len(container) == 0

    container.remove(func_b)

    assert len(container) == 0
