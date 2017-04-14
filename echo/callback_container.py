import weakref

__all__ = ['CallbackContainer']


class CallbackContainer(object):
    """
    A list of callback functions, which ...
    """

    def __init__(self):
        self.callbacks = []

    def _wrap(self, value):
        """
        """

        # We need to be careful with storing references to methods, because
        # if the callback method is on a class which contains both the callback
        # and the callback property, a circular reference is created which
        # results in a memory leak. Instead, we need to use a weak reference
        # which results in the callback being removed if the instance is
        # destroyed.

        if not callable(value):
            raise TypeError("Only callable values can be stored in CallbackContainer")

        elif self.is_bound_method(value):

            # We are dealing with a bound method. Method references aren't
            # persistent, so instead we store a reference to the function
            # and instance.

            value = (weakref.ref(value.__func__),
                     weakref.ref(value.__self__, self._auto_remove))

        return value

    def _auto_remove(self, method_instance):
        for value in self.callbacks[:]:
            if isinstance(value, tuple) and value[1] is method_instance:
                self.callbacks.remove(value)

    def __contains__(self, value):
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if isinstance(callback, tuple) and value.__func__ is callback[0]() and value.__self__ is callback[1]():
                    return True
            else:
                return False
        else:
            return value in self.callbacks

    def __iter__(self):
        for callback in self.callbacks:
            yield callback

    def __len__(self):
        return len(self.callbacks)

    @staticmethod
    def is_bound_method(func):
        return hasattr(func, '__func__') and getattr(func, '__self__', None) is not None

    def append(self, value):
        self.callbacks.append(self._wrap(value))

    def remove(self, value):
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if isinstance(callback, tuple) and value.__func__ is callback[0]() and value.__self__ is callback[1]():
                    self.callbacks.remove(callback)
        else:
            self.callbacks.remove(value)
