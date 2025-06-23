import weakref
from functools import partial

__all__ = ['CallbackContainer']


class CallbackContainer(object):
    """
    A list-like container for callback functions. We need to be careful with
    storing references to methods, because if a callback method is on a class
    which contains both the callback and a callback property, a circular
    reference is created which results in a memory leak. Instead, we need to use
    a weak reference which results in the callback being removed if the instance
    is destroyed. This container class takes care of this automatically.
    """

    def __init__(self):
        self.callbacks = []

    def clear(self):
        self.callbacks.clear()

    def _wrap(self, value, priority=0):
        """
        Given a function/method, this will automatically wrap a method using
        weakref to avoid circular references.
        """

        if not callable(value):
            raise TypeError("Only callable values can be stored in CallbackContainer")

        elif self.is_bound_method(value):

            # We are dealing with a bound method. Method references aren't
            # persistent, so instead we store a reference to the function
            # and instance.

            value = (weakref.ref(value.__func__),
                     weakref.ref(value.__self__, self._auto_remove),
                     priority)

        else:

            value = (value, priority)

        return value

    def _auto_remove(self, method_instance):
        # Called when weakref detects that the instance on which a method was
        # defined has been garbage collected.
        for value in self.callbacks[:]:
            if isinstance(value, tuple) and value[1] is method_instance:
                self.callbacks.remove(value)

    def __contains__(self, value):
        return self._contains(value)

    def _contains(self, value, priority=None):
        # Check if an entry matches the value and the priority, if not None
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if len(callback) == 3 and value.__func__ is callback[0]() and value.__self__ is callback[1]():
                    if priority is None or priority == callback[2]:
                        return True
            else:
                return False
        else:
            for callback in self.callbacks[:]:
                if len(callback) == 2 and value is callback[0]:
                    if priority is None or priority == callback[1]:
                        return True
            else:
                return False

    def iterate(self, use_priority=True, with_priority=False):
        if use_priority:
            iterator = sorted(self.callbacks, key=lambda x: x[-1], reverse=True)
        else:
            iterator = self.callbacks

        for callback in iterator:
            if len(callback) == 3:
                func = callback[0]()
                inst = callback[1]()
                # In some cases it can happen that the instance has been
                # garbage collected but _auto_remove hasn't been called, so we
                # just check here that the weakrefs were resolved
                if func is None or inst is None:
                    continue
                result = partial(func, inst)
            else:
                result = callback[0]
            if with_priority:
                yield result, callback[-1]
            else:
                yield result

    def __iter__(self):
        for callback in self.iterate():
            yield callback

    def __len__(self):
        return len(self.callbacks)

    @staticmethod
    def is_bound_method(func):
        return hasattr(func, '__func__') and getattr(func, '__self__', None) is not None

    def append(self, value, priority=0):
        # If we already have the same callback with the same priority, we can ignore
        if not self._contains(value, priority=priority):
            self.callbacks.append(self._wrap(value, priority=priority))

    def remove(self, value):
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if len(callback) == 3 and value.__func__ is callback[0]() and value.__self__ is callback[1]():
                    self.callbacks.remove(callback)
        else:
            for callback in self.callbacks[:]:
                if len(callback) == 2 and value is callback[0]:
                    self.callbacks.remove(callback)
